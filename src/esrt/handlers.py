import functools
import importlib
import json
from pathlib import Path
import sys
import typing as t

from pydantic import validate_call

from .typealiases import JsonActionT


@t.runtime_checkable
class HandlerProtocol(t.Protocol):
    def __call__(self, actions: t.Iterable[str], /) -> t.Iterable[JsonActionT]: ...


HandlerT = HandlerProtocol


@validate_call(validate_return=True)
def handle(actions: t.Iterable[str], /) -> t.Iterable[JsonActionT]:
    return map(json.loads, actions)


def import_from_string(import_str: str) -> t.Any:  # noqa: ANN401
    module_str, _, attrs_str = import_str.partition(':')
    if not module_str or not attrs_str:
        message = f'Import string "{import_str}" must be in format "module:attribute".'
        raise ImportError(message)
    module = importlib.import_module(module_str)
    try:
        return functools.reduce(getattr, attrs_str.split('.'), module)
    except AttributeError as exc:
        message = f'Attribute "{attrs_str}" not found in module "{module_str}".'
        raise ImportError(message) from exc


def add_cwd_to_sys_path() -> None:
    cwd = str(Path.cwd())
    sys.path.insert(0, cwd)
