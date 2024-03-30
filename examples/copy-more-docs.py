from copy import deepcopy
import json
import typing as t
import uuid


if __name__ == '__main__':
    for i, _ in enumerate(range(654321), start=1):
        d = {
            '_index': 'my-index-b',
            '_id': i,
            '_type': 'type1',
            '_source': {'field1': str(uuid.uuid4())},
        }
        print(json.dumps(d))


def handle(actions: t.Iterable[str]):
    for action in actions:
        d: dict[str, t.Any] = json.loads(action)
        yield d
        d2 = deepcopy(d)
        d2['_source']['field1'] += '!!!'
        d2['_source']['field2'] = str(uuid.uuid4())
        yield d2
