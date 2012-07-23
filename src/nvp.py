# -*- coding: utf-8 -*-
"""
"""

MAJOR_VERSION = 0
MINOR_VERSION = 0
PATCH_VERSION = 1
LABEL_VERSION = 'dev'

__version__ = '.'.join((
    MAJOR_VERSION,
    MINOR_VERSION,
    PATCH_VERSION,
))

if LABEL_VERSION:
    __version__ = '-'.join((__version__, LABEL_VERSION))

__author__ = 'Birk Nilson <birk@tictail.com>'
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


def dump():
    pass


def dumps():
    pass


def load():
    pass


def loads():
    pass
