import datetime
import time
try:
    from decimal import Decimal
except ImportError:
    # python 2.3 does not support Decimal
    # fallback to float at the loss of
    # precision
    Decimal = float

import constants

to_string = unicode

to_bytes = str

def parse_datetime(value):
    return datetime.datetime(*time.strptime(value, '%Y-%m-%d %H:%M:%S')[0:6])

def parse_date(value):
    return

def parse_time(value):
    pass

def to_set(value):
    return value.decode('ascii').split(',')

def raise_unsupported(value):
    raise ValueError("Unsupported type")

TYPE_MAP = {
    constants.FIELD_TYPE_DECIMAL        : Decimal,
    constants.FIELD_TYPE_TINY           : int,
    constants.FIELD_TYPE_SHORT          : int,
    constants.FIELD_TYPE_LONG           : int,
    constants.FIELD_TYPE_FLOAT          : float,
    constants.FIELD_TYPE_DOUBLE         : float,
    constants.FIELD_TYPE_NULL           : None,
    constants.FIELD_TYPE_TIMESTAMP      : parse_datetime,
    constants.FIELD_TYPE_LONGLONG       : int,
    constants.FIELD_TYPE_INT24          : int,
    constants.FIELD_TYPE_DATE           : parse_date,
    constants.FIELD_TYPE_TIME           : parse_time,
    constants.FIELD_TYPE_DATETIME       : parse_datetime,
    constants.FIELD_TYPE_YEAR           : int,
    constants.FIELD_TYPE_NEWDATE        : parse_date,
    #constants.FIELD_TYPE_VARCHAR        : to_string,
    constants.FIELD_TYPE_BIT            : int,
    constants.FIELD_TYPE_NEWDECIMAL     : Decimal,
    #constants.FIELD_TYPE_ENUM           : to_string,
    constants.FIELD_TYPE_SET            : to_set,
    constants.FIELD_TYPE_TINY_BLOB      : to_bytes,
    constants.FIELD_TYPE_MEDIUM_BLOB    : to_bytes,
    constants.FIELD_TYPE_LONG_BLOB      : to_bytes,
    constants.FIELD_TYPE_BLOB           : to_bytes,
    #constants.FIELD_TYPE_VAR_STRING     : to_string,
    #constants.FIELD_TYPE_STRING         : to_string,
    constants.FIELD_TYPE_GEOMETRY       : raise_unsupported,
}
