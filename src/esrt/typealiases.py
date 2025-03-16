import typing as t

from pydantic import JsonValue


JsonBodyT = dict[str, JsonValue]
JsonActionT = dict[str, JsonValue]

HttpMethod = t.Literal['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']
