import abc
import json
from pathlib import Path
import sys
import typing as t

from pydantic import validate_call

from .typealiases import JsonActionT


if t.TYPE_CHECKING:
    HandlerT = t.Callable[
        [t.Iterable[str]],
        t.Iterable[JsonActionT],
    ]
else:
    HandlerT = t.Callable
    doc_handler: HandlerT


@validate_call(validate_return=True)
def doc_handler(actions: t.Iterable[str], /) -> t.Iterable[JsonActionT]:
    return map(json.loads, actions)


class _BaseHandler(abc.ABC):
    def __init__(self, actions: t.Iterable[str]) -> None:
        self._iter = iter(actions)

    def __iter__(self) -> t.Iterator[JsonActionT]:
        return map(self.handle_one, self._iter)

    def __next__(self) -> JsonActionT:
        return next(self)

    @abc.abstractmethod
    def handle_one(self, action: str) -> JsonActionT: ...


class DocHandler(_BaseHandler):
    @validate_call(validate_return=True)
    def handle_one(self, action: str) -> JsonActionT:
        return json.loads(action)


def add_cwd_to_sys_path() -> None:
    cwd = str(Path.cwd())
    sys.path.insert(0, cwd)
