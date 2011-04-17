from dbapi import Connection as connect, paramstyle, apilevel, threadsafety
from errors import Warning, Error, \
                   InterfaceError, DatabaseError, \
                   InternalError, OperationalError, IntegrityError, \
                   InternalError, ProgrammingError, NotSupportedError
MySQLError = DatabaseError
