"""dbapi 2.0 paramstyle implementations"""

import re

class ParamFormatError(Exception):
    """Raised when there is a problem formatting a query according to a given
    paramstyle.
    """


class AbstractParamStyle(object):
    """Base class for formatting a query with a given paramstyle"""

    @property
    def is_positional(self):
        """Check whether or not this paramstyle supports positional arguments

        :returns: True if positional arguments are supported and False if named
        arguments are supported
        """
        raise NotImplementedError()

    @classmethod
    def format(cls, query, *args, **kwargs):
        """Format the given query with the given arguments or keyword
        arguments"""
        raise NotImplementedError()

class QmarkParamStyle(AbstractParamStyle):
    scanner = re.Scanner([
        (r"'((?:[^\\']|\\[^']|''|\\')*)'", None),
        (r'"((?:[^\\"]|\\[^"]|""|\\")*)"', None),
        (r'`((?:[^\\`]|\\[^`]|``|\\`)*)`', None),
        (r'\s+', None),
        (r'''[^?'"`]+''', None),
        (r'[?]', lambda x,y: (y, x.match.start(), x.match.end())),
    ])

    @classmethod
    def format(cls, query, *args, **kwargs):
        matches, unparsed = cls.scanner.scan(query)

        if unparsed:
            raise ParamFormatError("Error parsing query at offset %d" %
                    len(query) - len(unparsed))

        # offset into the query text
        offset = 0
        # list of query fragments - broken into text,replaced param[, text...]
        fragments = []
        for idx, (param, start, stop) in enumerate(matches):
            fragments.append(query[offset:start])
            fragments.append(args[idx])
            offset = stop
        if not fragments:
            return query
        else:
            return ''.join(fragments)

class NamedParamStyle(AbstractParamStyle):
    scanner = re.Scanner([
        (r"'(?:[^']|(?:\\[^'])|(?:'')|(?:\\'))*'", None),
        (r'"((?:[^\\"]|\\[^"]|""|\\")*)"', None),
        (r'`((?:[^\\`]|\\[^`]|``|\\`)*)`', None),
        (r'\s+', None),
        (r'''[^:'"`]+''', None),
        (r'[:][a-zA-Z0-9_]+', lambda x,y: (y, x.match.start(), x.match.end())),
    ])

    @classmethod
    def format(cls, query, **kwargs):
        matches, unparsed = cls.scanner.scan(query)

        print "matches => %r unparsed => %r" % (matches, unparsed)

        if unparsed:
            raise ParamFormatError("Error parsing query at offset %d" %
                    len(query) - len(unparsed))

        # offset into the query text
        offset = 0
        # list of query fragments - broken into text,replaced param[, text...]
        fragments = []
        for param, start, stop in matches:
            name = param[1:]
            fragments.append(query[offset:start])
            fragments.append(kwargs[name])
            offset = stop
        if not fragments:
            return query
        else:
            return ''.join(fragments)


class NumericParamStyle(AbstractParamStyle):
    scanner = re.Scanner([
        (r"'(?:[^']|(?:\\[^'])|(?:'')|(?:\\'))*'", None),
        (r'"((?:[^\\"]|\\[^"]|""|\\")*)"', None),
        (r'`((?:[^\\`]|\\[^`]|``|\\`)*)`', None),
        (r'\s+', None),
        (r'''[^:'"`]+''', None),
        (r'[:][0-9]+', lambda x,y: (y, x.match.start(), x.match.end())),
    ])

    @classmethod
    def format(cls, query, *args, **kwargs):
        if kwargs:
            raise ValueError("numeric paramstyle only supports "
                             "positional arguments")

        matches, unparsed = cls.scanner.scan(query)

        if unparsed:
            raise ParamFormatError("Error parsing query at offset %d" %
                    len(query) - len(unparsed))

        # offset into the query text
        offset = 0
        # list of query fragments - broken into text,replaced param[, text...]
        fragments = []
        for param, start, stop in matches:
            param_offset = int(param[1:])
            fragments.append(query[offset:start])
            fragments.append(args[param_offset])
            offset = stop
        if not fragments:
            return query
        else:
            return ''.join(fragments)

class FormatParamStyle(AbstractParamStyle):
    """DBAPI format formatting"""

    @classmethod
    def format(cls, query, *args, **kwargs):
        if kwargs:
            raise ValueError("format paramstyle does not support "
                             "named parameters")

        return query % args


class PyFormatParamStyle(AbstractParamStyle):
    @classmethod
    def format(cls, query, *args, **kwargs):
        if args:
            raise ValueError("pyformat paramstyle does not support "
                             "positional parameters")

        return query % kwargs


paramstyles = {
    'qmark' : QmarkParamStyle,
    'numeric' : NumericParamStyle,
    'named' : NamedParamStyle,
    'format' : FormatParamStyle,
    'pyformat' : PyFormatParamStyle,
}
