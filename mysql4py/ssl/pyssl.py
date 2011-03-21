# coding: utf-8
"""
    mysql4py.ssl.pyssl
    ~~~~~~~~~~~~~~~~~~

    Implements start_ssl for mysql4py using 'ssl' module
    available in python2.6+ and backported in some
    environments.

    :copyright: 2010-2011 by Andrew Garner
    :license: BSD, see LICENSE.rst for details
"""

import ssl

def start_ssl(sock, ssl_ca, ssl_client_cert, ssl_client_keyfile):
    """Start an SSL connection using ssl.wrap_socket"""
    return ssl.wrap_socket(sock,
                           cert_reqs=ssl.CERT_REQUIRED,
                           ca_certs=ssl_ca,
                           ssl_version=ssl.PROTOCOL_TLSv1)
            #ca_certs=ssl_ca_cert,
            #              certfile=ssl_client_cert,
            #              keyfile=ssl_client_keyfile)
