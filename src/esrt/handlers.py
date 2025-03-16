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
    def __init__(self, actions: t.Iterable[t.Union[str, ActionT]]) -> None:
        self._iter = iter(actions)

    def __iter__(self) -> t.Iterator[t.Union[str, ActionT]]:
        return map(self.handle_one, self._iter)

    def __next__(self) -> ActionT:
        return next(self)

    def handle_one(self, action: t.Union[str, ActionT]) -> t.Union[str, ActionT]:
        return t.cast('t.Union[str, ActionT]', action)


class DocHandler(BaseHandler):
    @validate_call(validate_return=True)
    def handle_one(self, action: Json) -> ActionT:
        """Use pydantic.validate_call to load JSON."""
        return action
