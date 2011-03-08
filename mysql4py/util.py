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
        if n_bytes is None:
            return self.data[index:]
        result = self.data[index:index + n_bytes]
        result[n_bytes-1]
        self.index += n_bytes
        return result

    def read_int8(self):
        """Read a 8-bit/one-byte integer from packet"""
        result = self.data[self.index]
        self.index += 1
        return result

    def read_int16(self):
        """Read a 16-bit/two-byte integer from packet"""
        index = self.index
        self.data[index+1] # index error check
        self.index += 2
        return struct.unpack('<H', self.data[index:index+2])[0]

    def read_int24(self):
        """Read a 24-bit/3-byte integer from packet"""
        index = self.index
        result = self.data[index:index+3]
        result[2] # length check
        result.append(0)
        self.index += 3
        return struct.unpack('<I', result)[0]

    def read_int32(self):
        """Read a 32-bit/3 byte integer from packet"""
        index = self.index
        result = self.data[index:index+4]
        result[3] # length check
        self.index += 4
        return struct.unpack('<I', result)[0]

    def read_int64(self):
        """Read a 64-bit/8 byte integer from packet"""
        index = self.index
        result = self.data[index:index+8]
        result[7] # length check
        self.index += 8
        return struct.unpack('<Q', result)[0]

    def skip(self, n_bytes):
        """Skip the requested number of bytes in packet"""
        self.index += n_bytes

    def read_lcb(self):
        """Read length code binary from this packet"""
        data = self.data
        index = self.index
        first = data[index]

        if first == 251: # NULL
            self.index += 1
            return None

        if first < 251:
            self.index += 1
            return first

        size = first - 250
        if size < 4:
            i_bytes = data[index+1:index+size+1]
            i_bytes[size-1] # length check
            # pad buffer to 4 bytes for struct.unpack
            i_bytes.extend([0]*(4 - size))
            # consume first byte + size bytes (either 2 or 3)
            self.index += size + 1
            return struct.unpack('<I', i_bytes)[0]
        else:
            # size > 250, but not null and not a 2 or 3 byte int
            # must be 64-bit integer
            i_bytes = data[index+1:index+8+1]
            i_bytes[7] # length check
            self.index += 8 + 1
            return struct.unpack('<Q', i_bytes)

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

    # we try to be atomic here, largely for the compressed protocol
    # XXX: pretty this up
    def read_n_lcs(self, n_fields):
        data = self.data
        index = self.index
        results = []
        append = results.append

        while n_fields:
            first = data[index]
            if first == 251: # NULL
                index += 1
                n_fields -= 1
                append(None)
                continue

            if first < 251:
                index += 1
                size = first
            else:
                size = first - 250
                if size < 4:
                    i_bytes = data[index+1:index+size+1]
                    i_bytes[size-1] # length check
                    # pad buffer to 4 bytes for struct.unpack
                    i_bytes.extend([0]*(4 - size))
                    # consume first byte + size bytes (either 2 or 3)
                    index += size + 1
                    size = struct.unpack('<I', i_bytes)[0]
                else:
                    # size > 250, but not null and not a 2 or 3 byte int
                    # must be 64-bit integer
                    i_bytes = data[index+1:index+8+1]
                    i_bytes[7] # length check
                    index += 8 + 1
                    size = struct.unpack('<Q', i_bytes)

            data[index+size - 1]
            index += size
            append(data[index-size:index].tostring())
            n_fields -= 1
        self.index = index
        return results

    def read_nullstr(self):
        """Read a null terminated string from this packet"""
        data = self.data
        index = self.index
        self.index = data.index(0x00) + 1
        return self.data[index:self.index - 1].tostring()
