from copy import deepcopy
import json
from random import choices
from string import ascii_letters
import typing as t


if __name__ == '__main__':
    for i in range(1, 2222):
        d = {
            '_index': 'my-index-b',
            '_id': i,
            '_type': 'type1',
            '_source': {'field1': ''.join(choices(ascii_letters, k=8))},
        }
        print(json.dumps(d))


def handle(actions: t.Iterable[str]):
    for action in actions:
        d: dict[str, t.Any] = json.loads(action)
        yield d
        d2 = deepcopy(d)
        d2['_source']['field1'] += '!!!'
        d2['_source']['field2'] = ''.join(choices(ascii_letters, k=8))
        yield d2
