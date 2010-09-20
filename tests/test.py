from channel import connect_unix
from protocol import Protocol

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

import time

report_interval = 50000
last = time.time()
proto.query('SELECT * FROM test.large_resultset')
print (proto.fields())
for i, row in enumerate(proto.rows()):
    #print row
    if i and not i % report_interval:
        now = time.time()
        print ("%d rows [%.2fus per row; %.2fs sampling interval]" %
                (i,
                 ((now - last)*1000000.0)/report_interval,
                 now-last
                )
              )
        last = now
