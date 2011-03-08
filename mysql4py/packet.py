import socket
import struct
import zlib
from array import array

from mysql4py.util import ByteStream
from mysql4py.errors import raise_mysql_error

def pkt2mysqlerror(data):
    errno, sqlstate = struct.unpack('<xH6s', data[0:9])
    msg = data[9:].decode('utf8')
    raise_mysql_error(errno, msg)

class Packet(ByteStream):
    __slots__ = ( 'size', 'seqno', 'data', 'index' )
    def __init__(self, size=None, seqno=0, data=None):
        self.size = size
        self.seqno = seqno
        self.data = data
        self.index = 0

    def is_ok_packet(self):
        """Check if this packet is an 'OK' packet"""
        return self.data[0] == 0x00

    def is_error_packet(self):
        """Check if this packet is an error packet"""
        return self.data[0] == 0xff

    def is_eof_packet(self):
        """Check if this packet is an EOF packet"""
        return self.data[0] == 0xfe


class CompressedPacket(Packet):
    def __init__(self, size=None, seqno=0, full_size=0, data=None):
        Packet.__init__(self, size, seqno, data)
        self.full_size = full_size

    def next_packet(self):
        """Return next logical packet from our buffers, or None
        if we do not have a full packet remaining"""
        try:
            size_seqno, = struct.unpack('<I', self.data[self.index:self.index+4])
        except struct.error:
            raise IndexError(self.data[self.index:])
        self.index += 4
        size, seqno = size_seqno & 0x00ffffff, size_seqno >> 24
        data = self.data[self.index:self.index+size]
        if len(data) < size:
            self.index -= 4 # unread header
            raise IndexError(self.data[self.index:])
        self.index += size
        if data[0] == 0xff:
            pkt2mysqlerror(data.tostring())
        return Packet(size, seqno, data)

class BasePacketStream(object):
    def __init__(self, channel):
        self.channel = channel

    def read(self, n_bytes):
        result = array('B')
        while n_bytes:
            chunk = self.channel.read(n_bytes)
            if not chunk:
                # MySQL server has gone away
                raise_mysql_error(errno=2006)
            result.extend(chunk)
            n_bytes -= len(chunk)
        return result

    def write(self, data):
        try:
            while data:
                n = self.channel.write(data)
                data = data[n:]
        except socket.error:
            raise_mysql_error(errno=2006)

    def next_packet(self):
        raise NotImplementedError()

    def send_packet(self, message, seqno=0):
        raise NotImplementedError()


class RawPacketStream(BasePacketStream):
    def next_packet(self):
        i, = struct.unpack('<I', self.read(4))
        size, seqno = i & 0x00ffffff, i >> 24
        data = self.read(size)
        if data[0] == 0xff:
            pkt2mysqlerror(data.tostring())

        while size == 0x00ffffff:
            i, = struct.unpack('<I', self.read(4))
            size, seqno = i & 0x00ffffff, i >> 24
            data.extend(self.read(size))
        size = len(data)
        return Packet(size, seqno, data)

    def send_packet(self, data, seqno=0):
        size = len(data)
        self.write(struct.pack('<I', size | (seqno << 24)) + data)



class CompressedPacketStream(BasePacketStream):
    def __init__(self, channel):
        BasePacketStream.__init__(self, channel)
        # maintain a buffer of any trailing data
        self.buffer = array('B')
        self.packet = None # partial data from last packet

    def next_compressed_packet(self, remaining=None):
        header = self.read(7)
        size_seq, uzlen0, uzlen1 = struct.unpack('<IHB', header)
        size, seqno = size_seq & 0x00ffffff, size_seq >> 24
        uzlen = uzlen0 | uzlen1 << 16
        buffer = array('B')

        if remaining:
            buffer.extend(remaining)

        data = self.read(size)

        if uzlen:
            buffer.fromstring(zlib.decompress(data))
        else:
            buffer.fromstring(data)

        return CompressedPacket(size, seqno, uzlen + len(remaining or ''), buffer)

    def next_packet(self):
        if not self.packet:
            self.packet = self.next_compressed_packet()

        try:
            pkt = self.packet.next_packet()
        except IndexError, exc:
            remaining = exc.args[0]
            self.packet = self.next_compressed_packet(remaining)
            pkt = self.packet.next_packet()
        return pkt

    def send_packet(self, data, seqno=0):
        # 4 byte packet header + size of payload (excluding 7-byte compression
        # header)
        total_size = 4 + len(data)
        size = len(data)
        payload = struct.pack('<I3xI',
                              total_size | (seqno << 24), # compression header
                              size | (seqno << 24)) + data
        self.write(payload)
