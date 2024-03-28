import json
from random import choices
from string import ascii_letters


def main():
    for i in range(1, 2222):
        d = {
            '_index': 'my-index-a',
            '_id': i,
            '_type': 'type1',
            '_source': {'field1': ''.join(choices(ascii_letters, k=8))},
        }
        print(json.dumps(d))


if __name__ == '__main__':
    main()
