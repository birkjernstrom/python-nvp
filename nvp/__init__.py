# -*- coding: utf-8 -*-
"""
Pythonic implementation of the NVP format.

NVP is in essence nothing else than regular HTTP query strings in
which keys can conform to one of three conventions in order to specify
their relationship - hierarchically - to each other.

For instance the query string::

    ?foo[0].a=1&foo[0].b=2&foo[1]='helloworld'&foobar=1337

Is intended to reflect the following hierarchical dictionary::

    {
        'foo': [
            {
                'a': 1,
                'b': 2
            },
            'helloworld'
        ],
        'foobar': 1337
    }

The shown query string utilized the bracket style of indicating sequences.
There are two other methods of achieving this in NVP. Sigh.

Instead of brackets parentheses are supported too. In which case the
previous query string could be re-written using this convention to::

    ?foo(0).a=1&foo(0).b=2&foo(1)='helloworld'&foobar=1337

The last method of indicating sequences is using the L_ key prefix.
Along with appending the index directly after the last key character.
In contrast with the bracket and parentheses convention the prefix type
cannot encode a dictionary which contains nested dictionaries or lists.

However, two-level dictionaries are allowed and will be encoded to::

    ?L_KEY0=3&L_KEY1=4&a=1&b=2

The NVP format was introduced by PayPal and is heavily utilized in
their API suites. More information about the format is thus best found
in their documentation at::

    http://bit.ly/ruw99i


However, although the list is short, other services utilize the format
in their API too. For instance Payson - a Swedish payment provider.

The purpose with this package is to enable more Pythonic implementations
of these APIs and to significantly ease communication with them.

This package will expose an API similar to ``simplejson``, ``marshal``
and ``pickle``, i.e using load & loads to decode and dump & dumps to encode.
"""

__author__ = 'Birk Nilson <birk@tictail.com>'
__version__ = '0.0.1-dev'
__all__ = [
    'util',
    'dump', 'dumps',
    'load', 'loads',
]


from urllib import urlencode
from urlparse import parse_qs
from nvp import util


###############################################################################
# ENCODING & DECODING API
###############################################################################

def dumps(obj, sequence_type=util.TYPE_SEQUENCE_BRACKET):
    """Encode given ``obj`` into an NVP query string.

    :param obj: The dictionary to encode
    :param sequence_type: The convention to utilize in encoding keys
                          corresponding to non-string sequences, e.g lists.
    """
    if not util.is_dict(obj):
        raise ValueError('Cannot NVP encode non-dict object: %s' % obj)

    pairs = util.get_hierarchical_pairs(obj, sequence_type=sequence_type)
    return urlencode(pairs)


def dump(fp, sequence_type=util.TYPE_SEQUENCE_BRACKET):
    """Encode given ``fp`` into an NVP query string.
    Where ``fp`` is a file-like object supporting the ``write` operation.`

    :param obj: The dictionary to encode
    :param sequence_type: The convention to utilize in encoding keys
                          corresponding to non-string sequences, e.g lists.
    """
    return dumps(fp.read(), sequence_type=sequence_type)


def loads(string,
          keep_blank_values=False,
          strict_parsing=False,
          strict_key_parsing=True,
          get_hierarchical=True):
    """Decode given NVP ``string`` into a dictionary.

    :param string: The encoded NVP string to decode
    :param keep_blank_values: Whether to retain keys with undefined values
    :param strict_parsing: Whether to use strict parsing of the query string
    :param strict_key_parsing: Whether to raise an exception in case errors
                               are found during parsing of given the NVP keys.
    :param get_hierarchical: Whether to decode into a single-level or
                             hierarchical dictionary.
    """
    # In case we receive an object which is considered False in an expression
    # we return an empty dictionary. The reason is because NVP is in essence
    # query strings in their encoded format, i.e they are expected to contain
    # key-value pairs.
    if not string:
        return {}

    # In case the value is not a string we consider it decoded since no other
    # type is allowed nor can be decoded in this implementation.
    if not util.is_string(string):
        return string

    unhierarchical = parse_qs(string,
                              keep_blank_values=keep_blank_values,
                              strict_parsing=strict_parsing)

    if not get_hierarchical:
        return unhierarchical
    return util.get_hierarchical_dict(unhierarchical,
                                      strict_key_parsing=strict_key_parsing)


def load(fp,
         keep_blank_values=False,
         strict_parsing=False,
         strict_key_parsing=True,
         get_hierarchical=True):
    """Decode given NVP ``fp`` into a dictionary.
    Where ``fp`` is a file-like object supporting the ``read`` operation.

    :param fp: File-like object supporting the read operation
    :param keep_blank_values: Whether to retain keys with undefined values
    :param strict_parsing: Whether to use strict parsing of the query string
    :param strict_key_parsing: Whether to raise an exception in case errors
                               are found during parsing of given the NVP keys.
    :param get_hierarchical: Whether to decode into a single-level or
                             hierarchical dictionary.
    """
    kwargs = locals()
    del kwargs['fp']
    return loads(fp.read(), **kwargs)
