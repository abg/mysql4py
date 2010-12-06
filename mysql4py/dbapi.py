# dbapi.py
import codecs

from channel import connect_unix, connect_tcp
from protocol import Protocol
from conversions import TYPE_MAP
from paramstyle import paramstyles as _paramstyles
from parser import OptionFile

DEFAULT_OPTION_PATHS = ['/etc/mysql/my.cnf', '/etc/my.cnf', '~/.my.cnf']

paramstyle = 'format'

class Connection(object):
    def __init__(self,
                 user=None, passwd=None,
                 db=None,
                 host='localhost', port=3306,
                 unix_socket=None,
                 ssl=False,
                 compress=False,
                 read_default_group=None,
                 read_default_file=None):

        if unix_socket:
            channel = connect_unix(unix_socket)
        else:
            channel = connect_tcp(host, port)
        self.protocol = Protocol(channel)

        if ssl:
            self.protocol.enable_ssl()
        if compress:
            self.protocol.enable_compression()

        if read_default_file or read_default_group:
            if not read_default_group:
                read_default_group = 'client'
            if not read_default_file:
                read_default_file = DEFAULT_OPTION_PATHS
            else:
                read_default_file = [read_default_file]
            options = OptionFile()
            options.read(read_default_file)
            auth_params = options.get(read_default_group, {})
            user = auth_params.get('user')
            passwd = auth_params.get('password')
            db = auth_params.get('db')

        self.protocol.authenticate(user, passwd, db)
        # toggle autocommit to off initially per dbapi spec
        self.autocommit()

    def autocommit(self):
        """Toggle auto-commit"""
        self.protocol.query('SET autocommit=0')

    def thread_id(self):
        """Fetch the current thread if of the underlying connection"""
        return self.protocol.info.thread_id

    def server_version(self):
        """Fetch the server version string from the MySQL instance this
        connection currently is connected to
        """
        return self.protocol.info.server_version

    def capabilities(self):
        """Fetch the integer flags this server supports.

        See constants.CLIENT_* settings for how to probe
        these.
        """
        return self.protocol.info.capabilities

    def capabilities_info(self):
        """Fetch the server capabilities as a string

        This is for debugging purposes only
        """
        return debug.capabilities(self.capabilities())

    def cursor(self):
        """Create a new cursor object to issue queries"""
        return Cursor(self)

    def close(self):
        """Close this connection

        All further operations on this connection or any open cursors will
        raise an exception.
        """
        self.protocol.close()

    def commit(self):
        """Commit any open transactions"""
        self.protocol.query('COMMIT')

    def rollback(self):
        """Rollback any open transactions"""
        self.protocol.query('ROLLBACK')


class Cursor(object):
    rowcount = -1
    description = None

    # Supported extension attributes
    rownumber = None
    connection = None
    messages = None
    lastrowid = None

    def __init__(self, connection):
        self.protocol = connection.protocol

    def callproc(procname, parameters=None):
        """Call a stored database procedure with the given name. The sequence
        of paramters must contain one entry for each argument that the
        procedure expects. The result of the call is returned as modified copy
        of the input sequence. Input parameters are left untouched, output and
        input/output paramters replaced with possibly new values.
        """
        raise NotImplementedError()
        self.protocol.query('CALL `%s`' % procname)
        return None

    def close(self):
        """Close this cursor"""
        self.protocol = None

    def execute(self, operation, params=()):
        """Close the cursor immediately.

        The cursor will be unusable from this point forward; an InterfaceError
        will be raised if any operation is attempted with the cursor
        """

        sql = _paramstyles[paramstyle].format(operation, *params)
        result = self.protocol.query(sql)
        if result:
            self.description = self.__fields_to_description(result.fields)
            self.iter = iter(result)
        else:
            self.description = None
            self.rowcount = result.affected_rows
            self.lastrowid = result.insert_id or None

        return self


    def executemany(operation, seq_of_params):
        """Prepare a database operation and then execute it against all
        parameter sequences or mappings found in the sequence seq_of_params
        """
        raise NotImplementedError()

    def __fields_to_description(self, fields):
        """Convert a list of protcol.Field instances into dbapiv2 compliant
        description tuples
        """
        for field in fields:
            if field.type_code in TYPE_MAP:
                field.convert = TYPE_MAP[field.type_code]
            else:
                field.convert = lambda value: codecs.utf_8_decode(value)[0]
        self.__fields = fields
        return [(field.column, None, None, None, None, None, None)
                    for field in fields]

    def fetchone(self):
        """Fetch the next row of the query result set"""
        return self.iter.next()

    def fetchmany(self, size=None):
        """Fetch the next set of rows of a query result, returning a sequence
        of sequences.  An empty sequence is returned when no more rows are
        available.

        The number of rows to fetch per call is specified by the paramter.  If
        it is not given, the cursor's arraysize determines the number of rows
        to be fetched.
        """
        while size:
            row = self.fetchone()
            yield row
            if row is None: break
            size -= 1

    def fetchall(self):
        """Fetch all remaining rows of a query result, returning them as a
        sequence of sequences.
        """
        return iter(self)

    def next(self):
        """Fetch the next available row from the cursor

        Raises StopIteration when no more rows are available

        PEP249 Optional Extension
        """
        row = self.fetchone()
        if row is None:
            raise StopIteration

    def nextset(self):
        """This method will make the cursor skip to the next available set,
        discarding any remaining rows from the current set.

        If there are no more sets, the method returns None
        """
        has_resultset, count = self.protocol.nextset()
        if has_resultset:
            self.description = self.__fields_to_description(self.protocol.fields())

            self.iter = self.protocol.rows()
        else:
            self.description = None
            self.rowcount = count
            self.__fields = None

    def scroll(value, mode='relative'):
        """Scroll the cursor in the result set to a new position according to
        mode
        """
        raise NotImplementedError()

    def setinputsizes(self, sizes):
        """Set sizes for input parameters.

        Not implemented
        """

    def setoutputsize(self, size, column=None):
        """Set a column buffer size for fetches of large columns.

        Not implemented
        """

    def __iter__(self):
        for row in self.iter:
            yield tuple([field.convert(column)
                         for column, field in zip(row, self.__fields)])

