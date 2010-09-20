# basic client flag constants
CLIENT_LONG_PASSWORD        = 1
CLIENT_FOUND_ROWS           = 2
CLIENT_LONG_FLAG            = 4
CLIENT_CONNECT_WITH_DB      = 8
CLIENT_NO_SCHEMA            = 16
CLIENT_COMPRESS             = 32
CLIENT_ODBC                 = 64
CLIENT_LOCAL_FILES          = 128
CLIENT_IGNORE_SPACE         = 256
CLIENT_PROTOCOL_41          = 512
CLIENT_INTERACTIVE          = 1024
CLIENT_SSL                  = 2048
CLIENT_IGNORE_SIGPIPE       = 4096
CLIENT_TRANSACTIONS         = 8192
CLIENT_RESERVED             = 16384
CLIENT_SECURE_CONNECTION    = 32768
CLIENT_MULTI_STATEMENTS     = 65536
CLIENT_MULTI_RESULTS        = 131072

# command constants
COM_QUIT                    = 0x01
COM_INIT_DB                 = 0x02
COM_QUERY                   = 0x03
COM_FIELD_LIST              = 0x04
COM_CREATE_DB               = 0x05
COM_DROP_DB                 = 0x06
COM_REFRESH                 = 0x07
COM_SHUTDOWN                = 0x08
COM_STATISTICS              = 0x09
COM_PROCESS_INFO            = 0x0a
COM_PROCESS_KILL            = 0x0c
COM_DEBUG                   = 0x0d
COM_PING                    = 0x0e
COM_CHANGE_USER             = 0x11
COM_BINLOG_DUMP             = 0x12
COM_TABLE_DUMP              = 0x13
COM_REGISTER_SLAVE          = 0x15
COM_STMT_PREPARE            = 0x16
COM_STMT_EXECUTE            = 0x17
COM_STMT_SEND_LONG_DATA     = 0x18
COM_STMT_CLOSE              = 0x19
COM_STMT_RESET              = 0x1a
COM_SET_OPTION              = 0x1b
COM_STMT_FETCH              = 0x1c

# server status constants
SERVER_STATUS_IN_TRANS              = 1
SERVER_STATUS_AUTOCOMMIT            = 2
SERVER_MORE_RESULTS_EXISTS          = 8
SERVER_QUERY_NO_GOOD_INDEX_USED     = 16
SERVER_QUERY_NO_INDEX_USED          = 32
SERVER_STATUS_CURSOR_EXISTS         = 64
SERVER_STATUS_LAST_ROW_SENT         = 128
SERVER_STATUS_DB_DROPPED            = 256
SERVER_STATUS_NO_BACKSLASH_ESCAPES  = 512
SERVER_STATUS_METADATA_CHANGED      = 1024

# Field types
FIELD_TYPE_DECIMAL      = 0x00
FIELD_TYPE_TINY         = 0x01
FIELD_TYPE_SHORT        = 0x02
FIELD_TYPE_LONG         = 0x03
FIELD_TYPE_FLOAT        = 0x04
FIELD_TYPE_DOUBLE       = 0x05
FIELD_TYPE_NULL         = 0x06
FIELD_TYPE_TIMESTAMP    = 0x07
FIELD_TYPE_LONGLONG     = 0x08
FIELD_TYPE_INT24        = 0x09
FIELD_TYPE_DATE         = 0x0a
FIELD_TYPE_TIME         = 0x0b
FIELD_TYPE_DATETIME     = 0x0c
FIELD_TYPE_YEAR         = 0x0d
FIELD_TYPE_NEWDATE      = 0x0e
FIELD_TYPE_VARCHAR      = 0x0f
FIELD_TYPE_BIT          = 0x10
FIELD_TYPE_NEWDECIMAL   = 0xf6
FIELD_TYPE_ENUM         = 0xf7
FIELD_TYPE_SET          = 0xf8
FIELD_TYPE_TINY_BLOB    = 0xf9
FIELD_TYPE_MEDIUM_BLOB  = 0xfa
FIELD_TYPE_LONG_BLOB    = 0xfb
FIELD_TYPE_BLOB         = 0xfc
FIELD_TYPE_VAR_STRING   = 0xfd
FIELD_TYPE_STRING       = 0xfe
FIELD_TYPE_GEOMETRY     = 0xff

# Field flags
NOT_NULL_FLAG       = 0x0001
PRI_KEY_FLAG        = 0x0002
UNIQUE_KEY_FLAG     = 0x0004
MULTIPLE_KEY_FLAG   = 0x0008
BLOB_FLAG           = 0x0010
UNSIGNED_FLAG       = 0x0020
ZEROFILL_FLAG       = 0x0040
BINARY_FLAG         = 0x0080
ENUM_FLAG           = 0x0100
AUTO_INCREMENT_FLAG = 0x0200
TIMESTAMP_FLAG      = 0x0400
SET_FLAG            = 0x0800

# convert a charset string to a mysql charset name/charset-number
py_to_mysql_charset = {
    'utf8'   : ('utf8', 33),      # utf8_general_ci
    'latin1' : ('latin1', 48),  # latin1_general_ci
}

# map a mysql charset number to a character set name
mysql_charsetnr_to_py_charset = {
    8       : 'latin1', # 8 = latin1_swedish_ci
}
