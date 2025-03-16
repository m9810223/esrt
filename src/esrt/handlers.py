from pathlib import Path
import sys
import typing as t

from pydantic import Json
from pydantic import validate_call

from .typealiases import ActionT


def add_cwd_to_sys_path() -> None:
    cwd = str(Path.cwd())
    sys.path.insert(0, cwd)


class BaseHandler:
    def __init__(self, actions: t.Iterable[str]) -> None:
        self._iter = iter(actions)

    def __iter__(self):  # noqa: ANN204
        return self.handle(self._iter)

    def __next__(self):  # noqa: ANN204
        return next(self._iter)

    def handle(self, actions: t.Iterable[str]):  # noqa: ANN201
        yield from map(self.handle_one, actions)

    def handle_one(self, action):  # noqa: ANN001, ANN201
        return action


class DocHandler(BaseHandler):
    @validate_call(validate_return=True)
    def handle_one(self, action: Json) -> ActionT:
        """Use pydantic.validate_call to load JSON."""
        return action
