import json
import typing as t

from esrt import DocHandler


# function style
def my_handler(actions: t.Iterable[str]):
    for action in actions:
        obj = json.loads(action)
        prefix = 'new-'
        if not t.cast(str, obj['_index']).startswith(prefix):
            obj['_index'] = prefix + obj['_index']
        yield obj


# class style
class MyHandler(DocHandler):
    def handle(self, actions: t.Iterable[str]):
        for action in actions:
            yield self.handle_one(action)

    def handle_one(self, action: str):
        obj = super().handle_one(action)
        prefix = 'new-'
        if not t.cast(str, obj['_index']).startswith(prefix):
            obj['_index'] = prefix + obj['_index']
        return obj
