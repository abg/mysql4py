
class Warning(StandardError):
    """Exception raised for important warnings like data
    truncations while inserting, etc.
    """

class Error(StandardError):
    """Exception that is the base class of all other error
    exceptions. You can use this to catch all errors with one
    single 'except' statement. Warnings are not considered
    errors and thus should not use this class as base.
    """
    def __init__(self, errno, message, sqlstate=None):
        StandardError.__init__(self, errno, message)
        self.sqlstate = sqlstate

class InterfaceError(Error):
    """Exception raised for errors that are related to the
    database interface rather than the database itself.
    """

class DatabaseError(Error):
    """Exception raised for errors that are related to the
    database.
    """

class DataError(DatabaseError):
    """Exception raised for errors that are due to problems with
    the processed data like division by zero, numeric value
    out of range, etc.
    """

class OperationalError(DatabaseError):
    """Exception raised for errors that are related to the
    database's operation and not necessarily under the control
    of the programmer, e.g. an unexpected disconnect occurs,
    the data source name is not found, a transaction could not
    be processed, a memory allocation error occurred during
    processing, etc.
    """

class IntegrityError(DatabaseError):
    """Exception raised when the relational integrity of the
    database is affected, e.g. a foreign key check fails.  It
    must be a subclass of DatabaseError.
    """

class InternalError(DatabaseError):
    """Exception raised when the database encounters an internal
    error, e.g. the cursor is not valid anymore, the
    transaction is out of sync, etc.
    """

class ProgrammingError(DatabaseError):
    """Exception raised for programming errors, e.g. table not
    found or already exists, syntax error in the SQL
    statement, wrong number of parameters specified, etc.
    """

class NotSupportedError(DatabaseError):
    """Exception raised in case a method or database API was used
    which is not supported by the database, e.g. requesting a
    .rollback() on a connection that does not support
    transaction or has transactions turned off.
    """

errno_to_exception = {
    # server errors
    1043 : InternalError,       # ER_BAD_HANDSHAKE
    1044 : OperationalError,    # ER_DBACCESS_DENIED
    1045 : OperationalError,    # ER_ACCESS_DENIED
    1046 : OperationalError,    # ER_NO_DB
    1047 : InternalError,       # ER_UNKNOWN_COM
    1048 : DataError,           # ER_BAD_NULL
    1049 : OperationalError,    # ER_BAD_DB
    1050 : OperationalError,    # ER_TABLE_EXISTS
    1051 : OperationalError,    # ER_BAD_TABLE
    1052 : OperationalError,    # ER_NON_UNIQ
    1053 : OperationalError,    # ER_SERVER_SHUTDOWN
    1054 : OperationalError,    # ER_BAD_FIELD
    1055 : ProgrammingError,    # ER_WRONG_FIELD_WITH_GROUP
    1056 : ProgrammingError,    # ER_WRONG_GROUP_FIELD
    1057 : ProgrammingError,    # ER_WRONG_SUM_SELECT
    1058 : ProgrammingError,    # ER_WRONG_VALUE_COUNT
    1059 : ProgrammingError,    # ER_TOO_LONG_IDENT
    1060 : ProgrammingError,    # ER_DUP_FIELDNAME
    1061 : DataError,           # ER_DUP_KEYNAME
    1062 : ProgrammingError,    # ER_DUP_ENTRY
    1063 : ProgrammingError,    # ER_WRONG_FIELD_SPEC
    1064 : ProgrammingError,    # ER_PARSE
    1065 : ProgrammingError,    # ER_EMPTY_QUERY
    1066 : ProgrammingError,    # ER_NONUNIQ_TABLE
    1067 : ProgrammingError,    # ER_INVALID_DEFAULT
    1068 : ProgrammingError,    # ER_MULTIPLE_PRI_KEY
    1069 : OperationalError,    # ER_TOO_MANY_KEYS
    1070 : OperationalError,    # ER_TOO_MANY_KEY_PARTS
    1071 : OperationalError,    # ER_TOO_LONG_KEY
    1072 : OperationalError,    # ER_KEY_COLUMN_DOES_NOT_EXIST

    # client errors
    2006 : OperationalError,
}

def raise_mysql_error(errno, message=''):
    """Raise the appropriate exception based on the given errno

    See:
        http://dev.mysql.com/doc/refman/5.5/en/error-handling.html
    """
    errorclass = errno_to_exception.get(errno, InternalError)
    raise errorclass(errno, message)
