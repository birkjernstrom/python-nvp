# -*- coding: utf-8 -*-
"""
NVP Utilities.

This is the workhorse module in the NVP package which is
in charge of implementing most of the logic while the core
NVP module is primarily intended to define the API.

"""


#: Type identifier corresponding to keys of type somekey[0]
CONVENTION_BRACKET = 'bracket'
#: Type identifier corresponding to keys of type somekey(0)
CONVENTION_PARENTHESES = 'parentheses'
#: Type identifier corresponding to keys of type L_SOMEKEY0
CONVENTION_UNDERSCORE = 'underscore'
#: The default type identifier to utilize if none other is specified
DEFAULT_CONVENTION = CONVENTION_UNDERSCORE

#: List of all available NVP conventions
CONVENTIONS = [
    CONVENTION_BRACKET,
    CONVENTION_PARENTHESES,
    CONVENTION_UNDERSCORE,
]

#: The string which identifies additional hierarchical depth
#: in key paths of type *bracket* and *parentheses*. In other words
#: the key path ``foo.bar`` should correspond to a dictionary
#: with the following structure: ``dict['foo']['bar']``
KEY_HIERARCHY_SEPARATOR = '.'

#: The string which identifies additional hierarchical depth
#: in key paths of type *underscore*. In other words the key path
#: ``FOO_BAR`` should correspond to a dictionary with the
#: following structure: ``dict['foo']['bar']``
KEY_UNDERSCORE_HIERARCHY_SEPARATOR = '_'


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
    return hasattr(obj, '__iter__') and not is_dict(obj)


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

def get_hierarchical_pairs(source,
                           convention=DEFAULT_CONVENTION,
                           key_filter=None):
    """Retrieve a list of tuples where the first item is the hierarchical
    key and the second its corresponding value.

    This list can be utilized along with ``urllib.urlencode`` in order
    to generate an NVP query string.

    :param source: The dictionary to convert into NVP pairs
    :param convention: The convention to utilize in encoding keys
                       corresponding to non-string sequences, e.g lists.
    :param key_filter: Function in which all keys should be filtered through.
                       Allowing key conversion from lowercase to uppercase
                       or vice versa for example.
    """
    if not is_dict(source):
        message = 'Cannot generate NVP pairs for non-dict object: %s'
        raise ValueError(message % source)

    return _convert_into_list(source, convention, key_filter=key_filter)


def get_hierarchical_dict(source):
    """Retrieve a hierarchical dictionary corresponding to the
    hierarchy defined in the keys of the given ``source`` directory.

    :param source: The single-level dictionary to convert
    """
    ret = {}
    sorted_keys = sorted(source.keys())
    convert = _convert_into_hierarchical_dict

    for key in sorted_keys:
        value = source[key]
        ret = convert(ret, key, value)
    return ret


###############################################################################
# KEY PATH FUNCTIONS
###############################################################################

def convert_underscore_into_bracket_key(key):
    """Convert given ``key`` of type ``underscore`` into the same
    hierarchical key in the ``bracket`` format.

        >>> import nvp.util
        >>> nvp.util.convert_underscore_into_bracket_key('L_FOO_0_BAR1')
        'L.FOO[0].BAR[1]'

    :param key: The key to convert
    """
    if key.find(KEY_UNDERSCORE_HIERARCHY_SEPARATOR) == -1:
        return key

    def gen_component(prefix, index):
        return generate_key_component(prefix, index,
                                      convention=CONVENTION_BRACKET)

    converted = []
    components = key.split(KEY_UNDERSCORE_HIERARCHY_SEPARATOR)
    for component in components:
        try:
            index = int(component)
            converted[-1] = gen_component(converted[-1], index)
        except ValueError:
            converted.append(component)

    # In case the value is sequential the underscore convention requires
    # the index to be appended to the last key component string. Strange
    # convention since all other sequential indexes are separated with
    # underscores to the neighbour keys.
    try:
        k, index = parse_underscore_key_with_index(converted[-1])
        converted[-1] = gen_component(k, index)
    except ValueError:
        pass

    return KEY_HIERARCHY_SEPARATOR.join(converted)


def detect_key_convention(key):
    """Detect whether given ``key`` represents a sequential value
    and which method we should utilize in case we need to parse
    it in order to retrieve the sanitized key along with the
    sequential index of its value.

        >>> import nvp.util
        >>> nvp.util.detect_key_convention('foobar[0]')
        'bracket'
        >>> nvp.util.detect_key_convention('foobar(0)')
        'parentheses'
        >>> nvp.util.detect_key_convention('FOOBAR0')
        'underscore'
        >>> nvp.util.detect_key_convention('foobar')
        'underscore'

    :param key: The key to check
    """
    last_character = key[-1]

    # Sequence with key following KEYNAME[0] standards
    if last_character == ']':
        return CONVENTION_BRACKET
    # Sequence with key following KEYNAME(0) standards
    elif last_character == ')':
        return CONVENTION_PARENTHESES
    return CONVENTION_UNDERSCORE


def parse_underscore_key_with_index(key):
    """Retrieve sequence index in given ``key`` along with the
    filtered key itself where ``key`` conforms to the underscore convention.

        >>> import nvp.util
        >>> nvp.util.parse_underscore_key_with_index('FOOBAR0')
        ('FOOBAR', 0)

    :param key: The key to retrieve sequence components from
    """
    index_at = 0
    while True:
        try:
            int(key[(index_at - 1)])
            index_at -= 1
        except ValueError:
            break

    if index_at:
        return (key[:index_at], int(key[index_at:]))

    message = 'Given key has no index appended to it: %s'
    raise ValueError(message % key)


def parse_bracket_key_with_index(key):
    """Retrieve sequence index in given ``key`` along with the
    filtered key itself where ``key`` conforms to the bracket convention.

        >>> import nvp.util
        >>> nvp.util.parse_bracket_key_with_index('foobar[0]')
        ('foobar', 0)

    :param key: The key to retrieve sequence components from
    """
    return _parse_group_key_with_index(key, '[', ']')


def parse_parentheses_key_with_index(key):
    """Retrieve sequence index in given ``key`` along with the
    filtered key itself where ``key`` conforms to the parentheses convention.

        >>> import nvp.util
        >>> nvp.util.parse_parentheses_key_with_index('foobar(0)')
        ('foobar', 0)

    :param key: The key to retrieve sequence components from
    """
    return _parse_group_key_with_index(key, '(', ')')


#: Mapping of conventions and their corresponding functions to
#: parse given key for key and index components
_KEY_PARSERS = {
    CONVENTION_BRACKET: parse_bracket_key_with_index,
    CONVENTION_PARENTHESES: parse_parentheses_key_with_index,
    CONVENTION_UNDERSCORE: parse_underscore_key_with_index,
}


def parse_key_with_index(key, convention=DEFAULT_CONVENTION):
    """Retrieve a tuple containing the sanitized value of the sequential
    ``key`` along with the list index contained in the raw ``key``.

    The method in which the index and sanitized key is detected is
    determined by given ``convention``. The supported types are::

        underscore
            KEYNAME0 -> (keyname, 0)
            KEYNAME1 -> (keyname, 1)
        bracket
            KEYNAME[0] -> (keyname, 0)
            KEYNAME[1] -> (keyname, 1)
        parentheses
            KEYNAME(0) -> (keyname, 0)
            KEYNAME(1) -> (keyname, 1)

    For instance in order to retrieve the components of a sequential
    key in the bracket format the following would be possible::

        >>> import nvp.util
        >>> nvp.util.parse_key_with_index('keyname[0]', 'bracket')
        '(keyname, 0)'

    :param key: The key to retrieve sequence_components from
    :param convention: The convention to utilize in encoding keys
                          corresponding to non-string sequences, e.g lists.
    """
    func = _KEY_PARSERS.get(convention, None)
    if func is not None:
        return func(key)

    message = 'Given convention is not one of the accepted values: %s'
    raise ValueError(message % CONVENTIONS)


def generate_key(components, convention=DEFAULT_CONVENTION):
    """Generate a valid NVP key which conforms to the given ``convention``.

    :param components: The key components to include in the generated key path
    :param convention: The convention to utilize in encoding keys
                          corresponding to non-string sequences, e.g lists.
    """
    if (convention == CONVENTION_BRACKET or
        convention == CONVENTION_PARENTHESES):
        return str(KEY_HIERARCHY_SEPARATOR).join(components)

    try:
        last_component = components[-1]
        key, index = last_component.split('_')
        components[-1] = '%s%s' % (key, index)
    except ValueError:
        pass

    return KEY_UNDERSCORE_HIERARCHY_SEPARATOR.join(components)


def generate_key_component(key, index, convention=DEFAULT_CONVENTION):
    """Generate sequence key component according to NVP convention of type
    specified in ``convention``.

    A key component is a slice of the entire key representing one level
    in the intended hierarchy. In other words the NVP key foo.bar[0]
    has two components; foo & bar[0] in which the latter in considered
    to be a sequence key since it contains a sequential value.

    :param key: The pure key without sequential index referencing
    :param index: The sequence index to encode in the sequence key
    :param convention: The convention to utilize in encoding keys
                          corresponding to non-string sequences, e.g lists.
    """
    if convention == CONVENTION_BRACKET:
        return '%s[%d]' % (key, index)

    if convention == CONVENTION_PARENTHESES:
        return '%s(%d)' % (key, index)

    if convention == CONVENTION_UNDERSCORE:
        return '%s%s%d' % (key, KEY_UNDERSCORE_HIERARCHY_SEPARATOR, index)

    message = 'Given convention is not one of the accepted values: %s'
    raise ValueError(message % CONVENTIONS)


###############################################################################
# INTERNAL FUNCTIONS
###############################################################################

def _parse_hierarchical_key_path(key):
    """Parse and retrieve a tuple reflecting the hierarchy
    defined in the given raw ``key``.

    The first item in the tuple is the parent key, i.e the key
    which will be set in the top-level dictionary of the hierarchical
    dictionary.

    The second item is a list of the remaining hierarchical keys
    which have not been parsed - they should when the recursive
    ``_convert_into_hierarchical_dict`` reaches their intended
    depth and they are - at that level - considered the parent
    key.

        >>> import nvp.util
        >>> nvp.util.parse_hierarchical_key_path('foo.bar.a.b')
        ('foo', ['bar', 'a', 'b'])
        >>> nvp.util.parse_hierarchical_key_path('foo.bar[0].a')
        ('foo', ['bar[0]', 'a'])
        >>> nvp.util.parse_hierarchical_key_path('FOO_BAR_0_A')
        ('FOO', ['BAR_0', 'A'])

    :param key: The raw key to retrieve hierarchy from
    """
    # Ensure we are dealing with a list of key components
    # rather than the string representation of the entire key path.
    if is_string(key):
        # Convert keys of type underscore into the bracket convention
        # prior to parsing them in order to avoid having to implement
        # separate logic for the type since it is quite a weird convention.
        key = convert_underscore_into_bracket_key(key)
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
    convention = detect_key_convention(initial_key)
    if not convention:
        return (initial_key, key)

    while True:
        try:
            initial_key, index = parse_key_with_index(initial_key, convention)
            key.insert(0, index)
        except ValueError:
            break
    return (initial_key, key)


def _parse_group_key_with_index(key, open_identifier, close_identifier):
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
                       convention,
                       key_filter=None,
                       destination=None,
                       keys=None):
    """Recursively convert given ``source`` dictionary into NVP
    pairs which are stored as tuples in the ``destination`` list.

    This list can be utilized along with ``urllib.urlencode`` in order
    to generate an NVP query string.

    :param source: The dictionary to convert into NVP pairs
    :param convention: The convention to utilize in encoding keys
                          corresponding to non-string sequences, e.g lists.
    :param key_filter: Function in which all keys should be filtered through.
                       Allowing key conversion from lowercase to uppercase
                       or vice versa for example.
    :param destination: The list in which pairs should be appended
    :param keys: List of key components in current NVP pair to generate
                 hierarchical key path from
    """
    source_is_dict = is_dict(source)
    source_is_sequential = is_non_string_sequence(source)

    # In case source is neither a dictionary nor a list
    # we have reached the end of the recursion required to
    # generate the current pair and we can return the entire
    # key along with the value - source in this case.
    if not (source_is_dict or source_is_sequential):
        # Assign current pair
        path_k = generate_key(keys, convention=convention)
        if key_filter is not None:
            path_k = key_filter(path_k)
        destination.append((path_k, source))
        return destination

    # Ensure both keys and destinations are initialized
    keys = keys if keys else []
    destination = destination if destination else []

    # Recursively convert all items in the current dictionary
    if source_is_dict:
        for k, v in source.iteritems():
            inner_keys = keys[:]
            inner_keys.append(k)
            destination = _convert_into_list(v, keys=inner_keys,
                                             convention=convention,
                                             key_filter=key_filter,
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
        k = generate_key_component(pk, index, convention=convention)

        inner_keys.append(k)
        index += 1

        destination = _convert_into_list(value, convention,
                                         key_filter=key_filter,
                                         destination=destination,
                                         keys=inner_keys)

    return destination


def _convert_into_hierarchical_dict(destination,
                                    keys,
                                    value):
    """Recursively convert given ``destination`` into a hierarchical
    dictionary which mirrors the hierarchy defined in the keys of the
    initial ``destination`` given.

    :param destination: The object in which all values should be assigned
    :param keys: List of components found in the single-level dictionary key
    :param value: The value to assign
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
        if is_non_string_sequence(value) and len(value) == 1:
            value = value[0]
        return value

    # Retrieve the current key, k, along with all the remaining keys
    # which are to be inserted in another iteration of this recursion.
    k, remaining_ks = _parse_hierarchical_key_path(keys)

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
                                                     value)

    return destination
