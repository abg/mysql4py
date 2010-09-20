from mysql4py.channel import connect_unix
from mysql4py.protocol import Protocol

endpoint = connect_unix('/var/lib/mysql/mysql.sock')
proto = Protocol(endpoint)
#proto.enable_ssl()
proto.enable_compression()
proto.authenticate(user='root')
proto.query('SHOW GRANTS')
proto.fields()
for row in proto.rows():
    print row
print (proto.query("SHOW SESSION STATUS LIKE '%SSL%'"))
print (proto.fields())
for row in proto.rows():
    print (row)

proto.query('SHOW SESSION variables LIKE "%char%"')
print proto.fields()
for row in proto.rows():
    print [row for row in row]

proto.query('SELECT 1, NOW(), "foo bar baz"')
print proto.fields()
for row in proto.rows():
    pass
