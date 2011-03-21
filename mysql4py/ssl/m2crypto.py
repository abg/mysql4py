# coding: utf-8
"""
    mysql4py.ssl.m2crypto
    ~~~~~~~~~~~~~~~~~~~~~

    Implements start_ssl for mysql4py using M2Crypto.
    This is a useful SSL fallback where python's ssl
    is not available.

    :copyright: 2010-2011 by Andrew Garner
    :license: BSD see LICENSE.rst for details
"""

import errno
from M2Crypto import SSL

def start_ssl(sock, ssl_ca_cert, ssl_client_cert, ssl_client_key):
    """Start SSL using m2crypto"""
    ctx = SSL.Context('sslv23')
    ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, depth=9)
    if ssl_ca_cert:
        ctx.load_verify_locations(ssl_ca_cert)
    sock = SSL.Connection(ctx, sock)
    sock.setup_ssl()
    sock.set_connect_state()
    try:
        sock.connect_ssl()
    except SSL.SSLError, exc:
        raise IOError(errno.EOPNOTSUPP, exc)
    return sock
