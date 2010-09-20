from dbapi import Connection

c = Connection(user='root')
z = c.cursor()
print z.execute('SELECT NOW(); SELECT 2; SELECT 32;', None)
for row in z:
    print row
print "nextset[1]: ", z.nextset()
for row in z:
    print row
print "nextset[2]: ", z.nextset()
for row in z:
    print row
c.close()
