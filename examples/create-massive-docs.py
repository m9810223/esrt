import json
from random import choices
from string import ascii_letters


if __name__ == '__main__':
    for i in range(1, 2222):
        d = {
            '_index': 'my-index-a',
            '_id': i,
            '_type': 'type1',
            '_source': {'field1': ''.join(choices(ascii_letters, k=8))},
        }
        print(json.dumps(d))
