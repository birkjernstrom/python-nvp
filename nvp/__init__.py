# -*- coding: utf-8 -*-
"""
"""




__author__ = 'Birk Nilson <birk@tictail.com>'
__version__ = '0.0.1-dev'
__all__ = [
    'dump', 'dumps',
    'load', 'loads',
]


from urllib import urlencode
from urlparse import parse_qs

#: The string which indicates a key path correlating to the
#: hierarchical relationship in which the associated value
#: is stored in the decoded dictionary. In other words the
#: encoded key path ``foo.bar`` corresponds to the value
#: stored in the decoded dictionary at ``dict['foo']['bar']``
KEY_HIERARCHY_SEPARATOR = '.'


###############################################################################
# ENCODING & DECODING API
###############################################################################

def dumps(obj):
    return urlencode(_convert_list_values(obj))


def dump():
    pass


def loads(string,
          keep_blank_values=False,
          strict_parsing=False,
          keep_list_values=True,
          get_hierarchical=True):
    """Decode given NVP string.

    """
    # In case we receive an object which is considered False in an expression
    # we return an empty dictionary. The reason is because NVP is in essence
    # query strings in their encoded format, i.e they are expected to contain
    # key-value pairs.
    if not string:
        return {}

    # In case the value is not a string we consider it decoded since no other
    # type is allowed nor can be decoded in this implementation.
    if not (hasattr(string, '__getitem__') and hasattr(string, 'join')):
        return string

    unhierarchical = parse_qs(string,
                              keep_blank_values=keep_blank_values,
                              strict_parsing=strict_parsing)

    if not keep_list_values:
        unhierarchical = _convert_list_values(unhierarchical)

    if not get_hierarchical:
        return unhierarchical

    hierarchical = get_hierarchical_dict(unhierarchical)
    return hierarchical


def load():
    pass


###############################################################################
# HELPER FUNCTIONS
###############################################################################

def get_hierarchical_dict(source):
    return source


###############################################################################
# INTERNAL FUNCTIONS
###############################################################################

def _convert_list_values(source):
    converted = {}
    for key, value in source.iteritems():
        if hasattr(value, '__getitem__'):
            if hasattr(value, 'setdefault'):
                value = _convert_list_values(value)
            elif hasattr(value, 'append'):
                value = value if len(value) > 1 else value[0]

        converted[key] = value
    return converted
