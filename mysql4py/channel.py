import socket
try:
    import ssl as sslmodule
except ImportError:
    sslmodule = None
from array import array

class BufferedChannel(object):
    BLOCK_SIZE = 4096

    def __init__(self, sock):
        self.socket = sock
        self.buf = array('B')
        self.size = 0

    def read(self, n_bytes):
        buf = self.buf
        size = self.size

        if size < n_bytes:
            recv = self.socket.recv
            while size < n_bytes:
                chunk = recv(4096)
                if not chunk:
                    raise socket.error("Socket EOF")
                size += len(chunk)
                buf.fromstring(chunk)

        self.size = size - n_bytes
        result = buf[0:n_bytes]
        del buf[0:n_bytes]
        return result

    def write(self, data):
        while data:
            n = self.socket.send(data)
            data = data[n:]
        return n

    def start_ssl(self, ssl_ca=None, ssl_key=None, ssl_cert=None, ssl_cipher=None):
        self.socket = sslmodule.wrap_socket(self.socket)

    def close(self):
        self.socket.close()

def connect_tcp(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    return BufferedChannel(sock)

def connect_unix(socket_path):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_path)
    return BufferedChannel(sock)
