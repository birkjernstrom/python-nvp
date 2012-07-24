# -*- coding: utf-8 -*-
#
# Generate NVP data source.
#
# The data source is stored in the JSON format since the intention is
# to allow developers to programatically generate test sources and execute
# them in an easy manner.
#

import json
import os.path

# Relative path to the file intended to contain the JSON data
DATA_FILENAME = '../../tests/resources/data.json'

# Dictionary containing encoded values
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
