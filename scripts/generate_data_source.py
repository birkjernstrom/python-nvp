# -*- coding: utf-8 -*-
#
# Generate NVP data source.
#
# The data source is stored in the JSON format since the intention is
# to allow developers to programatically generate test sources and execute
# them in an easy manner.
#
# This is primarily intended to be utilized during development of
# the NVP package.
#

import sys
import json
import os.path


def get_relative_as_abspath(path):
    return os.path.abspath(os.path.join(__file__, '../' + path))


# Insert the path of the source directory in which
# the local NVP module is located. Since the path is
# inserted in the beginning of the sys.path list the
# local version of the NVP module is ensured to be the one
# imported rather than one located in site-packages for instance.
sys.path.insert(0, get_relative_as_abspath('../'))

import nvp

# Relative path to the file intended to contain the JSON data
DATA_FILENAME = '../../tests/resources/data.json'

ENCODED = {
    'regular_url_query': 'FIRSTNAME=Robert&MIDDLENAME=Herbert&LASTNAME=Moore',
}

# Dictionary containing decoded values
DECODED = {
    'regular_url_query': {
        'FIRSTNAME': ['Robert'],
        'MIDDLENAME': ['Herbert'],
        'LASTNAME': ['Moore'],
    },
}

cbracket = nvp.util.CONVENTION_BRACKET
cparentheses = nvp.util.CONVENTION_PARENTHESES
cundersore = nvp.util.CONVENTION_UNDERSCORE

# Dictionary containing encoded values
ENCODED = {}
for name, dictionary in DECODED.iteritems():
    ENCODED[name] = {}
    for c in nvp.CONVENTIONS:
        ENCODED[name][c] = nvp.dumps(dictionary, convention=c)

# The data source to be JSON encoded
DATA = {
    'decoded': DECODED,
    'encoded': ENCODED,
}


def main():
    encoded_data = json.dumps(DATA, sort_keys=True, indent=4)
    path = os.path.abspath(os.path.join(__file__, DATA_FILENAME))
    with open(path, 'w') as f:
        f.write(encoded_data)

if __name__ == '__main__':
    main()
