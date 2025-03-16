import json
from pathlib import Path
import sys
import typing as t

from pydantic import Json
from pydantic import validate_call

from .typealiases import JsonActionT


if t.TYPE_CHECKING:
    HandlerT = t.Callable[
        [t.Iterable[str]],
        t.Iterable[JsonActionT],
    ]
else:
    HandlerT = t.Callable
    handle_json_str: HandlerT


def handle_json_str(actions: t.Iterable[str], /) -> t.Iterable[JsonActionT]:
    return map(json.loads, actions)


def add_cwd_to_sys_path() -> None:
    cwd = str(Path.cwd())
    sys.path.insert(0, cwd)


class BaseHandler:
    def __init__(self, actions: t.Iterable[t.Union[str, JsonActionT]]) -> None:
        self._iter = iter(actions)

    def __iter__(self) -> t.Iterator[t.Union[str, JsonActionT]]:
        return map(self.handle_one, self._iter)

    def __next__(self) -> JsonActionT:
        return next(self)

    def handle_one(self, action: t.Union[str, JsonActionT]) -> t.Union[str, JsonActionT]:
        return t.cast(t.Union[str, JsonActionT], action)


class DocHandler(BaseHandler):
    @validate_call(validate_return=True)
    def handle_one(self, action: Json) -> JsonActionT:
        """Use pydantic.validate_call to load JSON."""
        return action
