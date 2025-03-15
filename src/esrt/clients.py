import typing as t

from elasticsearch import Elasticsearch
from pydantic import JsonValue
from pydantic import validate_call

from .typealiases import BodyT


class Client:
    def __init__(self, host: str):
        self._client = Elasticsearch(hosts=host)

    @validate_call(validate_return=True)
    def ping(self) -> bool:
        return self._client.ping()  # type: ignore  # noqa: PGH003

    @validate_call(validate_return=True)
    def search(
        self,
        *,
        index: t.Optional[str] = None,
        doc_type: t.Optional[str] = None,
        body: t.Optional[BodyT] = None,
        params: t.Optional[dict[str, JsonValue]] = None,
    ) -> JsonValue:
        return self._client.search(index=index, doc_type=doc_type, body=body, params=params)

    @property
    @validate_call(validate_return=True)
    def hosts(self) -> list[dict[str, t.Any]]:
        return self._client.transport.hosts
