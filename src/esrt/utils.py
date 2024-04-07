from functools import reduce
import json
import typing as t


def parse_params(x: str, /) -> dict[str, str]:
    if x is None:
        return {}
    result = {}
    for pair in x.split('&'):
        if '=' in pair:
            k, v = pair.split('=', 1)
        else:
            k, v = pair, ''
        result[k] = v
    return result


def parse_header(x: str, /) -> dict[str, str]:
    if x is None:
        return {}
    return dict([x.split(':', 1)])


def merge_dicts(dicts: t.Optional[t.Iterable[dict[str, str]]], /):
    return reduce(lambda acc, x: {**acc, **x}, dicts or [], t.cast(dict[str, str], {}))


def json_obj_to_line(obj, /):
    if isinstance(obj, str):
        result = obj
    else:
        result = json.dumps(obj, ensure_ascii=False)
    if not result.endswith('\n'):
        return result + '\n'
    return result
