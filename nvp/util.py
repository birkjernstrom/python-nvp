# -*- coding: utf-8 -*-
"""
NVP Utilities.

This is the workhorse module in the NVP package which is
in charge of implementing most of the logic while the core
NVP module is primarily intended to define the API.

"""

import traceback


#: Type identifier corresponding to keys of type L_SOMEKEY0
TYPE_SEQUENCE_PREFIX = 'prefix'
#: Type identifier corresponding to keys of type somekey[0]
TYPE_SEQUENCE_BRACKET = 'bracket'
#: Type identifier corresponding to keys of type somekey(0)
TYPE_SEQUENCE_PARENTHESES = 'parentheses'
#: The default type identifier to utilize if none other is specified
TYPE_SEQUENCE_DEFAULT = TYPE_SEQUENCE_BRACKET


#: The string which indicates a key path correlating to the
#: hierarchical relationship in which the associated value
#: is stored in the decoded dictionary. In other words the
#: encoded key path ``foo.bar`` corresponds to the value
#: stored in the decoded dictionary at ``dict['foo']['bar']``
KEY_HIERARCHY_SEPARATOR = '.'


###############################################################################
# TYPE HELPERS - MOSTLY DUCK TYPING SHORTCUTS
###############################################################################

def is_string(obj):
    """Check whether given ``obj`` is a ``str``.

    :param obj: The object to duck-type for str attributes
    """
    return hasattr(obj, '__getitem__') and hasattr(obj, 'join')


def is_int(obj):
    """Check whether given ``obj`` is an ``int``.

    :param obj: The object to duck-type for int attributes
    """
    return hasattr(obj, '__pow__') and hasattr(obj, 'denominator')


def is_dict(obj):
    """Check whether given ``obj`` is a ``dict``.

    :param obj: The object to duck-type for dict attributes
    """
    return hasattr(obj, '__getitem__') and hasattr(obj, 'setdefault')


def is_non_string_sequence(obj):
    """Check whether given ``obj`` is either
    a ``tuple``, ``list``, ``set`` or ``frozenset``.

    :param obj: The object to duck-type for sequence attributes
    """
    return (hasattr(obj, '__getitem__') and
            not hasattr(obj, 'join') and
            not hasattr(obj, 'setdefault'))


def sequence_has_index(sequence, index):
    """Check whether given ``sequence`` has a value assigned
    at given ``index``.

    :param sequence: The sequence to check against
    :param index: The index to check whether it exists or not
    """
    try:
        sequence[index]
        return True
    except IndexError:
        return False


###############################################################################
# ENCODING & DECODING FUNCTIONS
###############################################################################

def get_hierarchical_pairs(source, sequence_type=TYPE_SEQUENCE_DEFAULT):
    """Retrieve a list of tuples where the first item is the hierarchical
    key and the second its corresponding value.

    This list can be utilized along with ``urllib.urlencode`` in order
    to generate an NVP query string.

    :param source: The dictionary to convert into NVP pairs
    :param sequence_type: The convention to utilize in encoding keys
                          corresponding to non-string sequences, e.g lists.
    """
    if not is_dict(source):
        message = 'Cannot generate NVP pairs for non-dict object: %s'
        raise ValueError(message % source)

    return _convert_into_list(source, sequence_type)


def get_hierarchical_dict(source, strict_key_parsing=True):
    """Retrieve a hierarchical dictionary corresponding to the
    hierarchy defined in the keys of the given ``source`` directory.

    :param source: The single-level dictionary to convert
    :param strict_key_parsing: Whether to raise an exception in case
                               errors are found during parsing of the
                               given key.
    """
    ret = {}
    sorted_keys = sorted(source.keys())
    convert = _convert_into_hierarchical_dict

    for key in sorted_keys:
        value = source[key]
        ret = convert(ret, key, value, strict_key_parsing=strict_key_parsing)
    return ret


###############################################################################
# KEY PATH FUNCTIONS
###############################################################################

def parse_hierarchical_key_path(key, strict_key_parsing=True):
    """Parse and retrieve a tuple reflecting the hierarchy
    defined in the given raw ``key``.

    The first item in the tuple is the parent key, i.e the key
    which will be set in the top-level dictionary of the hierarchical
    dictionary.

    The second item is a list of keys representing children of the
    parent key. In case the key is a string a dictionary is intended.
    Otherwise an integer is returned in which case a list is expected.

        >>> import nvp.util
        >>> nvp.util.parse_hierarchical_key_path('foo.bar.a.b')
        ('foo', ['bar', 'a', 'b'])
        >>> nvp.util.parse_hierarchical_key_path('foo.bar[0].a')
        ('foo', ['bar', 0, 'a'])

    :param key: The raw key to retrieve hierarchy from
    :param strict_key_parsing: Whether to raise an exception in case
                               errors are found during parsing of the
                               given key.
    """
    # Ensure we are dealing with a list of key components
    # rather than the string representation of the entire key path.
    if is_string(key):
        key = key.split(KEY_HIERARCHY_SEPARATOR)

    # In case the initial key item in the list of components is not
    # a string we can return both the initial and remaining key
    # components directly. Because in such case the key path has
    # already been parsed.
    initial_key = key.pop(0)
    if not is_string(initial_key):
        return (initial_key, key)

    # Check whether the initial key is a representation of a
    # sequence value, i.e list or tuple. Otherwise, there is
    # no need to continue parsing the key path.
    sequence_type = get_sequence_key_type(initial_key)
    if not sequence_type:
        return (initial_key, key)

    try:
        components = get_sequence_key_components(sequence_type, initial_key)
        initial_key, index = components
        key.insert(0, index)
        return (initial_key, key)
    except ValueError:
        if strict_key_parsing:
            traceback.print_exc()
            raise
    return (initial_key, key)


def get_sequence_key_type(key):
    """Detect whether given ``key`` represents a sequential value
    and which method we should utilize in case we need to parse
    it in order to retrieve the sanitized key along with the
    sequential index of its value.

        >>> import nvp.util
        >>> nvp.util.get_sequence_key_type('foobar')
        False
        >>> nvp.util.get_sequence_key_type('foobar[0]')
        'bracket'
        >>> nvp.util.get_sequence_key_type('foobar(0)')
        'parentheses'
        >>> nvp.util.get_sequence_key_type('L_FOOBAR0')
        'prefix'

    :param key: The key to check
    """
    # Sequence with key following L_KEYNAME0 standards.
    # Although PayPal seems to treat this case-sensitively our
    # implementation will support case-insensitive cases of
    # this prefix. In order to allow lowercasing of those keys.
    if key.startswith('L_') or key.startswith('l_'):
        return TYPE_SEQUENCE_PREFIX

    last_character = key[-1]

    # Sequence with key following KEYNAME[0] standards
    if last_character == ']':
        return TYPE_SEQUENCE_BRACKET
    # Sequence with key following KEYNAME(0) standards
    elif last_character == ')':
        return TYPE_SEQUENCE_PARENTHESES
    return False


def get_key_prefix_sequence_components(key):
    """Retrieve sequence components in given ``key``
    which uses L_ prefixes to identify sequence indexes.

        >>> import nvp.util
        >>> nvp.util.get_key_parentheses_sequence_components('L_FOOBAR0')
        ('FOOBAR', 0)

    :param key: The key to retrieve sequence components from
    """
    pass


def get_key_bracket_sequence_components(key):
    """Retrieve sequence components in given ``key``
    which uses parentheses to identify sequence indexes.

        >>> import nvp.util
        >>> nvp.util.get_key_bracket_sequence_components('foobar[0]')
        ('foobar', 0)

    :param key: The key to retrieve sequence components from
    """
    return _get_key_group_sequence_components(key, '[', ']')


def get_key_parentheses_sequence_components(key):
    """Retrieve sequence components in given ``key``
    which uses brackets to identify sequence indexes.

        >>> import nvp.util
        >>> nvp.util.get_key_parentheses_sequence_components('foobar(0)')
        ('foobar', 0)

    :param key: The key to retrieve sequence components from
    """
    return _get_key_group_sequence_components(key, '(', ')')


#: Mapping of sequence types and their corresponding functions
#: for retrieving sequence components related to the given key.
_SEQUENCE_KEY_FUNCS = {
    TYPE_SEQUENCE_PREFIX: get_key_prefix_sequence_components,
    TYPE_SEQUENCE_BRACKET: get_key_bracket_sequence_components,
    TYPE_SEQUENCE_PARENTHESES: get_key_parentheses_sequence_components,
}


def get_sequence_key_components(sequence_type, key):
    """Retrieve a tuple containing the sanitized value of the sequential
    ``key`` along with the list index contained in the raw ``key``.

    The method in which the index and sanitized key is detected is
    determined by given ``sequence_type``. The supported types are::

        prefix
            L_KEYNAME0 -> (keyname, 0)
            L_KEYNAME1 -> (keyname, 1)
        bracket
            KEYNAME[0] -> (keyname, 0)
            KEYNAME[1] -> (keyname, 1)
        parentheses
            KEYNAME(0) -> (keyname, 0)
            KEYNAME(1) -> (keyname, 1)

    For instance in order to retrieve the components of a sequential
    key in the bracket format the following would be possible::

        >>> import nvp.util
        >>> nvp.util.get_sequence_key_components('bracket', 'keyname[0]')
        '(keyname, 0)'

    :param sequence_type: The convention to utilize in encoding keys
                          corresponding to non-string sequences, e.g lists.
    :param key: The key to retrieve sequence_components from
    """
    func = _SEQUENCE_KEY_FUNCS.get(sequence_type, None)
    if func is not None:
        return func(key)

    message = 'Given sequence_type is not one of the accepted values: %s'
    raise ValueError(message % _SEQUENCE_KEY_FUNCS.keys())


def generate_sequence_key(key, index, sequence_type=TYPE_SEQUENCE_DEFAULT):
    """Generate sequence key according to NVP convention of type
    specified in ``sequence_type``.

    :param key: The pure key without sequential index referencing
    :param index: The sequence index to encode in the sequence key
    :param sequence_type: The convention to utilize in encoding keys
                          corresponding to non-string sequences, e.g lists.
    """
    if sequence_type == TYPE_SEQUENCE_BRACKET:
        return '%s[%d]' % (key, index)

    if sequence_type == TYPE_SEQUENCE_PARENTHESES:
        return '%s(%d)' % (key, index)

    if sequence_type == TYPE_SEQUENCE_PREFIX:
        return 'L_%s%d' % (key, index)

    message = 'Given sequence_type is not one of the accepted values: %s'
    raise ValueError(message % _SEQUENCE_KEY_FUNCS.keys())


###############################################################################
# INTERNAL FUNCTIONS
###############################################################################

def _get_key_group_sequence_components(key, open_identifier, close_identifier):
    """Retrieve a tuple containing the sanitized value of the sequential
    ``key`` along with the list index contained in the raw ``key``.

    :param key: The key to parse
    :param open_identifier: The character which identifies the beginning of
                            the index specification in the given key
    :param open_identifier: The character which identifies the end of
                            the index specification in the given key
    """
    try:
        open_index = key.rindex(open_identifier)
        close_index = key.rindex(close_identifier)
    except ValueError:
        message = 'Missing opening or closing sequence identifier for key: %s'
        raise ValueError(message % key)

    try:
        index = int(key[(open_index + 1):close_index])
    except ValueError:
        message = 'Cannot retrieve numerical index in key: %s'
        raise ValueError(message % key)
    return (key[:open_index], index)


def _convert_into_list(source,
                       sequence_type,
                       destination=None,
                       keys=None,
                       depth=0):
    """Recursively convert given ``source`` dictionary into NVP
    pairs which are stored as tuples in the ``destination`` list.

    This list can be utilized along with ``urllib.urlencode`` in order
    to generate an NVP query string.

    :param source: The dictionary to convert into NVP pairs
    :param sequence_type: The convention to utilize in encoding keys
                          corresponding to non-string sequences, e.g lists.
    :param destination: The list in which pairs should be appended
    :param keys: List of key components in current NVP pair to generate
                 hierarchical key path from
    :param depth: The current depth of the recursion
    """
    # Bail in case sequence type 'prefix' is requested and given
    # source directory contains nested dictionaries or lists.
    if depth > 1 and sequence_type == TYPE_SEQUENCE_PREFIX:
        message = 'Maximum encoding depth reached for type: prefix'
        raise ValueError(message)

    source_is_dict = is_dict(source)
    source_is_sequential = is_non_string_sequence(source)

    # In case source is neither a dictionary nor a list
    # we have reached the end of the recursion required to
    # generate the current pair and we can return the entire
    # key along with the value - source in this case.
    if not (source_is_dict or source_is_sequential):
        # Assign current pair
        path_k = str(KEY_HIERARCHY_SEPARATOR).join(keys)
        destination.append((path_k, source))
        return destination

    # Ensure both keys and destinations are initialized
    keys = keys if keys else []
    destination = destination if destination else []

    # Recursively convert all items in the current dictionary
    if source_is_dict:
        for k, v in source.iteritems():
            keys.append(k)
            destination = _convert_into_list(v, keys=keys, depth=(depth + 1),
                                             sequence_type=sequence_type,
                                             destination=destination)

        return destination

    # Now when source is a non-string sequence we have to retrieve
    # the previous item in the keys list in order to generate a valid
    # key, since the current key will be an integer - the index of the
    # value to store for the final key path. Since this function is recursive
    # we do not need to iterate through all the keys to find the nearest
    # string to utilize as the parent key. Because the previous recursion
    # will have concatinated both its previous key along with the index
    # of the containing sequence in which this key is located.
    pk = keys.pop()
    if not pk:
        message = 'Cannot generate sequence key without parent key: %s'
        raise ValueError(message % source)

    index = 0
    for value in source:
        inner_keys = keys[:]
        k = generate_sequence_key(pk, index, sequence_type=sequence_type)
        inner_keys.append(k)
        index += 1

        destination = _convert_into_list(value, sequence_type,
                                         destination=destination,
                                         keys=inner_keys, depth=(depth + 1))

    return destination


def _convert_into_hierarchical_dict(destination,
                                    keys,
                                    value,
                                    strict_key_parsing=True):
    """Recursively convert given ``destination`` into a hierarchical
    dictionary which mirrors the hierarchy defined in the keys of the
    initial ``destination`` given.

    :param destination: The object in which all values should be assigned
    :param keys: List of components found in the single-level dictionary key
    :param value: The value to assign
    :param strict_key_parsing: Whether to raise an exception in case errors
                               are found during parsing of the initial keys
                               in the single-level dictionary.
    """
    # Since this function is recursive we might end up with an empty
    # list of keys. In which case we should return the sanitized value
    # by design; the return value of this iteration will be the value
    # assigned to the key in the iteration which executed this one.
    if not keys:
        # Prior to being converted all values in the NVP query string
        # will be stored in lists as per HTTP RFC recommendations.
        # However, since NVP does not utilize this convention and
        # explicitly defines the hierarchy there is no need to adhere
        # to this convention. In case we had we would end up with nested
        # lists in all scenarios which defeats the point. Therefore, we
        # retrieve the value of item instead in cases where a
        # single-item list is given.
        if len(value) == 1:
            value = value[0]
        return value

    kwargs = dict(strict_key_parsing=strict_key_parsing)

    # Retrieve the current key, k, along with all the remaining keys
    # which are to be inserted in another iteration of this recursion.
    k, remaining_ks = parse_hierarchical_key_path(keys, **kwargs)

    # Check whether we are intended to set a key in a dict or append to a list
    is_current_sequential = is_non_string_sequence(destination)

    # We need to be aware of whether the next recursion has the intention
    # of appending values to a list or set keys in a dictionary. Thus
    # we check whether the next key in the list is an integer - in which
    # case we need to initialize a list in this recursion rather than
    # a dictionary which is default.
    try:
        is_next_sequential = is_int(remaining_ks[0])
    except (IndexError, ValueError):
        is_next_sequential = False

    # Assign either an empty list or dictionary to target which will be
    # the variable assigned to destination[k] unless it has already
    # been initialized in a previous recursion.
    target = [] if is_next_sequential else {}

    # Ensure we initialize destination[k] prior to assigning values to it.
    if is_current_sequential and not sequence_has_index(destination, k):
        destination.insert(k, target)
    elif not is_current_sequential and k not in destination:
        destination[k] = target

    destination[k] = _convert_into_hierarchical_dict(destination[k],
                                                     remaining_ks,
                                                     value, **kwargs)

    return destination
