import mysql4py

c = mysql4py.connect(user='root')
z = c.cursor()

for key, value in z.execute('SHOW GLOBAL STATUS'):
    print "%s = %s" % (key, value)
