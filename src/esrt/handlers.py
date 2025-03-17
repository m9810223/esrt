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
    handle: HandlerT


@validate_call(validate_return=True)
def handle(actions: t.Iterable[str], /) -> t.Iterable[JsonActionT]:
    return map(json.loads, actions)


def add_cwd_to_sys_path() -> None:
    cwd = str(Path.cwd())
    sys.path.insert(0, cwd)
