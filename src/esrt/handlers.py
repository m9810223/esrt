from contextlib import redirect_stdout
import json
import sys
import typing as t


class BaseHandler:
    def __init__(self, actions: t.Iterable[str]):
        self._iter = iter(actions)

    def __iter__(self):
        return self.handle(self._iter)

    def __next__(self):
        return next(self._iter)

    def handle(self, actions: t.Iterable[str]):
        for action in actions:
            yield self.handle_one(action)

    def handle_one(self, action):
        return action

    @staticmethod
    def print(*args, **kwargs):
        with redirect_stdout(sys.stderr):
            print(*args, **kwargs)


class DocHandler(BaseHandler):
    def handle_one(self, action: str):
        return json.loads(action)
