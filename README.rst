Introduction
============
This is yet another pure-python implementation of the MySQL protocol. Other
interesting (and more mature) implementations include:

* pymysql_
* myconnpy_

.. _pymysql: http://code.google.com/p/pymysql
.. _myconnpy: https://launchpad.net/myconnpy

This implementation aims at full support for the MySQL protocol and to provide
an interface to extended functionality such as the replication protocol and
prepared statements.

Current features supported are:

* LOAD DATA LOCAL INFILE
* Multiple resultsets
* SSL auth (incomplete; no x509, no cert verification)
* large BLOB handling (currently broken for compressed protocol)
* Compressed protocol
* Pure iterator interface (can read large results with fairly low memory usage)

TODO:

* PEP249 support is incomplete
* charset handling is incomplete
* SSL auth needs to support x509 and should verify certs
* BLOB support (only supported for raw protocol, not compressed)
* Prepared statement protocol
* Improved character set support
* Integrate binlog protocol parsing
* Context managers for connection/cursor objects

Future plans:

* Optional C speedups to address network and protocol decoding bottlenecks

Example
=======

::

  import mysql4py
  
  conn = mysql4py.connect(user='root', unix_socket='/tmp/mysql.sock')
  cursor = conn.cursor()
  
  for key, value in cursor.execute('SHOW GLOBAL STATUS'):
      print "%s = %s" % (key, value)
