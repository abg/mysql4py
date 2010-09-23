from mysql4py.channel import connect_unix
from mysql4py.protocol import Protocol

endpoint = connect_unix('/var/lib/mysql/mysql.sock')
proto = Protocol(endpoint)
#proto.enable_ssl()
#proto.enable_compression()
proto.authenticate(user='root')
result = proto.query('SHOW GRANTS')

if result:
    for row in result:
        print row

result = proto.query("SHOW SESSION STATUS LIKE '%SSL%'")
if result:
    for row in result:
        print (row)

result = proto.query('SHOW SESSION variables LIKE "%char%"')
for row in result:
    print [row for row in row]

result = proto.query('SELECT 1, NOW(), "foo bar baz"')
for row in result:
    pass
