"""MySQL protocol support"""

from struct import pack
try:
    from hashlib import sha1
except ImportError:
    from sha import new as sha1

import packet
import constants
from errors import InterfaceError, OperationalError

# default to 16MB
MAX_PACKET_SIZE = 2**24


STATE_INIT      = 0   # initial state before anything is done
STATE_AUTH      = 2   # middle of authenticating
STATE_READY     = 4   # ready to issue command
STATE_FIELDS    = 8   # reading field data (call fields())
STATE_DATA      = 16  # reading row data (call rows())
STATE_RESULT    = 32  # another resultset is available (call nextset())

def protected_state(state):
    """Wrap a `Protocol` method and raise an exception if method is called
    in an incorrect order, or would interrupt an on-going operation
    """
    def wrapper(func):
        """Basic wrapper around the function. Runs dispatch"""
        def dispatch(protocol, *args, **kwargs):
            """Only run the requested function if we are in the correctly
            configured state"""
            if protocol.state != state:
                raise InterfaceError(-666, "Expected state: %r Current state: %r"
                        % (state, protocol.state))
            return func(protocol, *args, **kwargs)
        return dispatch
    return wrapper

class Protocol(object):
    """Base Protocol class"""

    def __init__(self, channel, charset='utf8'):
        self.channel = channel
        self.state = STATE_INIT
        self.info = None
        # set in the authetnicate reply to enable features
        self.flags = 0
        self.packet = packet.RawPacketStream(channel)
        self.charset = charset

        # SSL params
        self.ssl_ca = None

        # active result, if any
        self.result = None

    # These raise InterfaceError if called anytime after server handshake
    # (self.server_info is not None)
    def enable_ssl(self, ssl_ca, ssl_key, ssl_cert):
        """Enable SSL support"""
        self.flags |= constants.CLIENT_SSL
        self.ssl_ca = ssl_ca
        self.ssl_key = ssl_key
        self.ssl_cert = ssl_cert

    def enable_compression(self):
        """Enable compression support"""
        self.flags |= constants.CLIENT_COMPRESS

    def requested_feature(self, flag):
        """Check if a feature has been requested of the protocol"""
        return self.flags & flag

    # Send authentication reply to server
    # This raises an InterfaceError if called anytime after server handshake
    # (self.server_info is not None)
    # when ssl is enabled will start an ssl handshake and send the password
    # separately
    #
    # when compression is enabled, pktio is switched out for the compressed
    # packet stream once auth is complete
    #@protected_state(STATE_INIT)
    def authenticate(self, user=None, password=None, schema=None):
        """Authenticate to a MySQL server"""
        self.info = Handshake.decode(self.packet.next_packet())
        flags = self.info.server_capabilities & \
                     ~(constants.CLIENT_SSL|
                       constants.CLIENT_COMPRESS|
                       #constants.CLIENT_LOCAL_FILES|
                       constants.CLIENT_INTERACTIVE|
                       constants.CLIENT_NO_SCHEMA)
        flags |= (constants.CLIENT_MULTI_RESULTS|
                  constants.CLIENT_MULTI_STATEMENTS|
                  constants.CLIENT_SECURE_CONNECTION
                 )

        # enable compression and/or ssl, if requested
        self.flags |= flags

        authentication = self.__authenticate_plain
        if self.requested_feature(constants.CLIENT_SSL):
            if not self.info.supports_feature(constants.CLIENT_SSL):
                raise OperationalError(2026,
                                       "SSL connection error "
                                       "(SSL not supported by server)")
            authentication = self.__authenticate_ssl

        if self.requested_feature(constants.CLIENT_COMPRESS) and \
                not self.info.supports_feature(constants.CLIENT_COMPRESS):
            raise OperationalError(1157, # (?)ER_NET_UNCOMPRESS_ERROR
                                   "Server does not support compression")

        token = scramble(password, self.info.salt)

        if not authentication(user, token, schema):
            # fallback to 3.23 style crypt() passwords
            self.__send_old_password(password, self.info.salt[0:8])

        if self.requested_feature(constants.CLIENT_COMPRESS):
            # all future packets will use the compressed format after auth
            # switch to the compressed_packet parser
            self.packet = packet.CompressedPacketStream(self.channel)

        self.state = STATE_READY

    def __authenticate_plain(self, user, token, schema):
        """Standard (non-ssl) authentication.  Uses 4.1 auth by default
        w/ fallback to 3.23 old_passwords mode if necessary
        """
        # send auth_reply with all parameters
        # raises OperationalError on complete failure
        # returns False on EOF (server requested 3.23 password fallback)
        # returns True otherwise
        auth = ClientAuthentication(user=user,
                                    token=token,
                                    schema=schema,
                                    charset=33, # utf8
                                    client_flags=self.flags,
                                    max_packet_size=MAX_PACKET_SIZE)
        self.packet.send_packet(auth.serialize(), seqno=1)
        pkt = self.packet.next_packet()
        return pkt.is_ok_packet()

    def __authenticate_ssl(self, user, token, schema):
        """SSL authentication.  Sends first reply packet, performs
        an SSL handshake and then resends the reply with the password
        token
        """
        # send a AuthReply to server w/o password
        # do SSL handshake
        # send a 2nd AuthReply to server w/ password
        auth = ClientAuthentication(user=user,
                                    token=None,
                                    schema=schema,
                                    charset=33, # utf8
                                    client_flags=self.flags,
                                    max_packet_size=MAX_PACKET_SIZE)
        self.packet.send_packet(auth.serialize(), seqno=1)
        try:
            self.channel.start_ssl(ssl_ca=self.ssl_ca,
                                   ssl_cert=self.ssl_cert,
                                   ssl_key=self.ssl_key)
        except IOError, exc:
            raise OperationalError(2026, "SSL connection error: %s" % exc)
        auth.token = token
        self.packet.send_packet(auth.serialize(), seqno=2)
        pkt = self.packet.next_packet()
        return pkt.is_ok_packet()

    def __send_old_password(self, password, salt):
        """Send the requested password token in 3.23 format.

        If a password is in old_password format the server will reply
        with an EOF packet. The client is supposed to reply with an
        additional packet containing just the password
        """
        # send a packet containing just the scrambled password token
        token = scramble_323(password, salt)
        self.packet.send_packet(token, seqno=3)
        # ignore response - if it's an error the generator will raise it
        self.packet.next_packet()

    def close(self):
        message = pack('B', constants.COM_QUIT)
        self.packet.send_packet(message, seqno=0)
        self.channel.close()

    def ping(self):
        """Check the connection to the server

        :raises: OperationalError if the connection is down
        """
        message = pack('B', constants.COM_PING)
        self.packet.send_packet(message, seqno=0)
        self.state = STATE_RESULT
        self.nextset()
        return True

    def sync(self):
        while self.state != STATE_READY:
            for row in self.result: pass
            self.nextset()

    # simple com_query interface
    # raises InternalError if called with an active resultset
    # state != OK
    #@protected_state(STATE_READY)
    def query(self, sql):
        """Send a simple query to the server"""
        # just send the query and set our state to 'needs the results
        # processed'. Errors are delayed until nextset() is run
        self.sync()
        assert self.state == STATE_READY, \
            "Query in state %d but expected STATE_READY"
        message = pack('B', constants.COM_QUERY) + sql.encode(self.charset)
        self.packet.send_packet(message, seqno=0)
        self.state = STATE_RESULT

    #@protected_state(STATE_RESULT)
    def nextset(self):
        """Process the next resulset

        Returns result
        """
        if self.state != STATE_RESULT:
            return None

        response = self.packet.next_packet()
        # OK packet -> INSERT/UPDATE/etc. only rows affected/insert_id
        # returned
        if response.is_ok_packet():
            self.result = SimpleResult(response)
            if self.result.more_results():
                self.state = STATE_RESULT
            else:
                self.state = STATE_READY

            return self.result
        # LOAD DATA LOCAL INFILE response
        elif response.data[0] == 0xfb:
            # packet[0] = \xfb
            # packet[1:] = file we should load
            # send multiple packets of file data
            response.skip(1) # skip the known 0xfb byte
            try:
                fileobj = open(response.read_all().tostring(), 'rb')
            except IOError, exc:
                # Sending an empty packet
                self.packet.send_packet(''.encode(self.charset), seqno=2)
                self.state = STATE_READY
                raise

            try:
                data = fileobj.read(65535)
                pktnr = 2
                while data:
                    self.packet.send_packet(data, pktnr)
                    data = fileobj.read(65535)
                    pktnr += 1
                self.packet.send_packet(''.encode(self.charset), pktnr)
                self.state = STATE_READY
            finally:
                fileobj.close()

            pkt = self.packet.next_packet()
            response = SimpleResult(pkt)
            if response.more_results():
                self.state = STATE_RESULT
            else:
                self.state = STATE_READY
            return response
        else:
            self.result = ResultSet(response, self)
            self.state = STATE_DATA
            return self.result

class SimpleResult(object):
    def __init__(self, response):
        self.info = OK.decode(response)

    # some useful properties
    #@property
    def affected_rows(self):
        return self.info.affected_rows
    affected_rows = property(affected_rows)

    #@property
    def insert_id(self):
        return self.info.insert_id
    insert_id = property(insert_id)

    def more_results(self):
        return self.info.server_status & constants.SERVER_MORE_RESULTS_EXISTS

    def next(self):
        raise StopIteration

    def __iter__(self):
        return self

    def __nonzero__(self):
        # False = not a resultset
        return False

class ResultSet(object):
    def __init__(self, response, protocol):
        self.field_count = response.read_lcb()
        self.protocol = protocol
        self.fields = self.__fields()

    #@protected_state(STATE_FIELDS)
    def __fields(self):
        """Find the fields for the current resultset

        Returns list of `Field` instances
        """
        fields = []

        pkt = self.protocol.packet.next_packet()
        while not pkt.is_eof_packet():
            fields.append(Field.decode(pkt))
            pkt = self.protocol.packet.next_packet()
        self.protocol.state = STATE_DATA
        return fields

    #@protected_state(STATE_DATA)
    def __iter__(self):
        """Iterate over the rows returned by the current resultset

        This is a pure iterator.  Rows are not cached in anyway and once
        iterated, one cannot go back.  Caller is responsible for buffering
        rows if requested.
        """
        if not self.protocol:
            raise StopIteration
        n_fields = self.field_count
        next_packet = self.protocol.packet.next_packet
        pkt = next_packet()
        #for pkt in self.packet:
        while not pkt.data[0] == 0xfe:
            if pkt.data[0] == 0xfe:
                break
            yield tuple(pkt.read_n_lcs(n_fields))
            pkt = next_packet()
        info = EOF.decode(pkt)
        if info.status & constants.SERVER_MORE_RESULTS_EXISTS:
            self.protocol.state = STATE_RESULT
        else:
            self.protocol.state = STATE_READY

        self.protocol = None

    def __nonzero__(self):
        # True = is a resultset and can be iterated over
        return True

class Handshake(object):
    """Initial server handshake"""
    def __init__(self,
                 protocol_version=None,
                 server_version=None,
                 thread_id=None,
                 salt=None,
                 server_capabilities=None,
                 charset=None,
                 server_status=None):
        self.protocol_version = protocol_version
        self.server_version = server_version
        self.thread_id = thread_id
        self.salt = salt
        self.server_capabilities = server_capabilities
        self.charset = charset
        self.server_status = server_status

    def supports_feature(self, flag):
        """Check whether the server supports a given feature"""
        return self.server_capabilities & flag

    #@staticmethod
    def decode(pkt):
        """Decode a RawPacket into a Handshake instance"""
        protocol_version = pkt.read_int8()
        server_version = pkt.read_nullstr()
        thread_id = pkt.read_int32()
        salt = pkt.read(8)
        pkt.skip(1)
        server_capabilities = pkt.read_int16()
        charset = pkt.read_int8()
        server_status = pkt.read_int16()
        pkt.skip(13)
        salt += pkt.read(12)
        return Handshake(protocol_version=protocol_version,
                         server_version=server_version,
                         thread_id=thread_id,
                         salt=salt,
                         server_capabilities=server_capabilities,
                         charset=charset,
                         server_status=server_status)
    decode = staticmethod(decode)

class ClientAuthentication(object):
    """Client reply to server handshake"""
    def __init__(self,
                 client_flags=0,
                 max_packet_size=None,
                 charset=33,
                 user='',
                 token='',
                 schema=''):
        if max_packet_size is None:
            max_packet_size = MAX_PACKET_SIZE
        self.client_flags = client_flags
        self.max_packet_size = max_packet_size
        self.charset = charset
        self.user = user
        self.token = token
        self.schema = schema

    def serialize(self):
        """Serialize this authentication request into the packed
        wire format required by the MySQL protocol
        """
        NUL = '\x00'.encode('utf8')
        packed_data = pack('<IIB23x',
                                  self.client_flags,
                                  self.max_packet_size,
                                  self.charset)
        packed_data += (self.user or '').encode('utf8')
        packed_data += NUL # null terminated user name
        packed_data += chr(len(self.token or '')).encode('utf8')
        packed_data += (self.token or '').encode('utf8') # LCB password
        packed_data += (self.schema or '').encode('utf8')
        packed_data += NUL # null terminated schema
        return packed_data

class OK(object):
    def __init__(self,
                 affected_rows,
                 insert_id,
                 server_status,
                 warning_count,
                 message):
        self.affected_rows = affected_rows
        self.insert_id = insert_id
        self.server_status = server_status
        self.warning_count = warning_count
        self.message = message

    #@staticmethod
    def decode(pkt):
        pkt.skip(1) # skip field_count, always 0x00
        affected_rows = pkt.read_lcb()
        insert_id = pkt.read_lcb()
        server_status = pkt.read_int16()
        warning_count = pkt.read_int16()
        message = pkt.read()

        return OK(affected_rows,
                  insert_id,
                  server_status,
                  warning_count,
                  message)
    decode = staticmethod(decode)


class EOF(object):
    """End-of-Field/End-of-Data protocol message"""
    def __init__(self, warnings, status):
        self.warnings = warnings
        self.status = status

    #@staticmethod
    def decode(pkt):
        """Decode a RawPacket into an EOF message"""
        pkt.skip(1)
        warnings = pkt.read_int16()
        status = pkt.read_int16()
        return EOF(warnings=warnings, status=status)
    decode = staticmethod(decode)


class Field(object):
    """Field descriptor protocol message"""
    __slots__ = (
        'schema',
        'table',
        'column',
        'type_code',
        'charset',
        'convert',
        'flags',
    )

    def __init__(self, schema, table, column, type_code, charset, flags):
        self.schema = schema
        self.table = table
        self.column = column
        self.type_code = type_code
        self.charset = charset
        self.flags = flags

    @staticmethod
    def decode(pkt):
        """Decode a field packet"""
        pkt.read_lcs() # catalog
        schema = pkt.read_lcs()
        table = pkt.read_lcs()
        pkt.read_lcs() # org_table
        column = pkt.read_lcs()
        pkt.read_lcs() # org_name
        pkt.skip(1)
        charset = pkt.read_int16()
        pkt.read_int32() # display length
        type_code = pkt.read_int8()
        flags = pkt.read_int16()
        #pkt.skip(1) # "scale"/decimals
        #pkt.skip(2) # filler
        #default = pkt.read_lcb()

        return Field(schema=schema,
                     table=table,
                     column=column,
                     type_code=type_code,
                     charset=charset,
                     flags=flags)

    def __repr__(self):
        return ("Field(schema=%r,table=%r,column=%r,type=%r,"
                "charset=%r,flags=%r)") % (
                self.schema, self.table, self.column,
                self.type_code, self.charset, self.flags
               )

# Normal RowData is just a series of LCB fields
# Probably worth building in some more intelligent logic here
class RowData(object):
    """Row data protocol message"""

    #@staticmethod
    def decode(pkt, n_fields):
        """Decode a raw packet into a set of values

        A RowData packet is always a series of length-coded strings
        """
        return pkt.read_n_lcs(n_fields)
    decode = staticmethod(decode)

def scramble(password, message):
    """Generate a hashed password suitable for passing to MySQL 4.1+

    For servers using old_passwords, use scramble323
    """
    if not password:
        # always return a bytestring
        return ''.encode('utf8')

    stage1 = sha1(password).digest()
    stage2 = sha1(stage1).digest()
    stage3 = sha1()
    stage3.update(message)
    stage3.update(stage2)
    stage1 = array.array('B', stage1)
    stage3 = array.array('B', stage3.digest())
    return array.array('B',
                       [a ^ b for a, b in zip(stage1, stage3)]).tostring()

def scramble_323(password, message):
    """Scramble a password in the old (insecure) format"""

    def hash_password(password):
        """Generate a password hash in 323 format

        Returns password as two 4-byte integers
        """
        nr  = 1345345333L
        add = 7
        nr2 = 0x12345671

        for char in password:
            # skip whitespace in password
            if chr(char) in " \t":
                continue
            tmp = char
            nr ^= (((nr & 63) + add)*tmp) + (nr << 8)
            nr2 += (nr2 << 8) ^ nr
            add += tmp

        return nr & ((1L << 31) -1L), nr2 & ((1L << 31) -1L)

    def random_323(seed1, seed2):
        """Seeded pseudo-random generator used for 3.23 password
        scrambling.

        Adapted from libmysql/password.c for python2.3+
        """
        max_value = 0x3FFFFFFF
        seed1 = seed1 % max_value
        seed2 = seed2 % max_value

        while True:
            seed1 = (seed1*3 + seed2) % max_value
            seed2 = (seed1 + seed2 + 33) % max_value
            yield float(seed1) / float(max_value)

    if not password:
        return ''.encode('utf8')

    token = password.encode('utf8')

    hash_pass = hash_password(token)
    hash_mesg = hash_password(message)
    next_rand = random_323(hash_pass[0] ^ hash_mesg[0],
                           hash_pass[1] ^ hash_mesg[1]).next
    result = [int(next_rand()*31) + 64 for i in xrange(8)]
    extra = int(next_rand()*31)
    result = [i ^ extra for i in result]
    #result += '\x00'.encode('utf8')

    return pack('8B', result)
