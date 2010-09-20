import struct

class ByteStream(object):
    """A seekable byte stream

    Expects a data object that provides integer values, such as a
    py3 byearray or array('B')
    """

    def __init__(self, data):
        self.index = 0
        self.data = data

    def read(self, n_bytes=None):
        """Read the requested number of bytes from this packet chain"""
        index = self.index
        result = self.data[index:index + n_bytes]
        self.index += len(result)
        return result

    def read_int8(self):
        """Read a 8-bit/one-byte integer from packet"""
        self.index += 1
        return self.data[self.index - 1]

    def read_int16(self):
        """Read a 16-bit/two-byte integer from packet"""
        index = self.index
        self.index += 2
        return struct.unpack('<H', self.data[index:index+2])[0]

    def read_int24(self):
        """Read a 24-bit/3-byte integer from packet"""
        index = self.index
        self.index += 3
        return struct.unpack('<I', self.data[index:index+3] + '\x00')[0]

    def read_int32(self):
        """Read a 32-bit/3 byte integer from packet"""
        index = self.index
        self.index += 4
        return struct.unpack('<I', self.data[index:index+4])[0]

    def read_int64(self):
        """Read a 64-bit/8 byte integer from packet"""
        index = self.index
        self.index += 8
        return struct.unpack('<Q', self.data[index:index+8])[0]

    def skip(self, n_bytes):
        """Skip the requested number of bytes in packet"""
        self.index += n_bytes

    def read_lcb(self):
        """Read length code binary from this packet"""
        data = self.data
        first = data[self.index]
        self.index += 1
        if first == 0xfb: # NULL
            return None

        elif first <= 250: # UNSIGNED_CHAR_COLUMN
            return first
        elif first == 252: # UNSIGNED_SHORT_COLUMN
            return self.read_int16()
        elif first == 253: # UNSIGNED_INT24_COLUMN
            return self.read_int24()
        elif first == 254: # UNSIGNED_INT64_COLUMN
            return self.read_int64()

    def read_lcs(self):
        """Read a length coded binary from packet"""
        data = self.data
        first = data[self.index]
        self.index += 1

        if first < 251:
            size = first
        elif first == 0xfb: # NULL
            return None
        elif first == 252:
            size = self.read_int16()
        elif first == 253:
            size = self.read_int24()
        elif first == 254:
            size = self.read_int64()

        if size:
            return self.read(size).tostring()

    def read_n_lcs(self, n_fields):
        data = self.data
        index = self.index
        results = []
        append = results.append
        while n_fields:
            #size = self.read_lcb()
            first = data[index]
            index += 1
            if first == 0xfb:
                append(None)
            if first <= 250:
                append(data[index:index+first].tostring())
                index += first
            else:
                l = first - 250
                b = data[index:index+l]
                if l <= 4:
                    b.fromstring('\x00'*(4-l))
                    z, = struct.unpack('<I', b)
                else:
                    b.fromstring('\x00'*(8-l))
                    z, = struct.unpack('<Q', b)
                index += l
                append(data[index:index+z].tostring())
                index += z
            n_fields -= 1
        return results

    def read_nullstr(self):
        """Read a null terminated string from this packet"""
        data = self.data
        index = self.index
        self.index = data.index(0x00) + 1
        return self.data[index:self.index - 1]
