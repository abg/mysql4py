import mysql4py

c = mysql4py.connect(read_default_group='client')
z = c.cursor()
z.execute('SHOW GLOBAL VARIABLES LIKE %s', ('socket',))
import pprint
pprint.pprint(list(z))

z = c.cursor()

z.execute('SELECT USER()', ())

pprint.pprint(list(z))
