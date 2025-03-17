import json
import typing as t



def handle(actions: t.Iterable[str]):
    for action in actions:
        obj = json.loads(action)
        prefix = 'new-'
        if not t.cast(str, obj['_index']).startswith(prefix):
            obj['_index'] = prefix + obj['_index']
        yield obj
