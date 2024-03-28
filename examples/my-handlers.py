import json
import typing as t

from esrt import DocHandler


class MyHandler(DocHandler):
    def handle_one(self, action: str):
        obj = json.loads(action)
        prefix = 'new-'
        if not t.cast(str, obj['_index']).startswith(prefix):
            obj['_index'] = prefix + obj['_index']
        return obj


# function style
def my_handler(actions: t.Iterable[str]):
    for action in actions:
        yield json.loads(action)
