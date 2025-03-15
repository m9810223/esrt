import typing as t

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
from pydantic import JsonValue
from pydantic import validate_call

from .typealiases import BodyT


class Client:
    def __init__(self, host: str) -> None:
        self._client = Elasticsearch(hosts=host)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}({self.hosts})>'

    @property
    @validate_call(validate_return=True)
    def hosts(self) -> list[dict[str, t.Any]]:
        return self._client.transport.hosts

    @validate_call(validate_return=True)
    def ping(self) -> bool:
        return bool(self._client.ping())

    @validate_call(validate_return=True)
    def info(self) -> JsonValue:
        return self._client.info()

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

    @validate_call(validate_return=True)
    def scan(
        self,
        *,
        query: t.Optional[BodyT] = None,  # ?
        scroll: str,
        #
        index: t.Optional[str] = None,
        doc_type: t.Optional[str] = None,
    ) -> t.Generator[dict[str, JsonValue], None, None]:
        return scan(
            client=self._client,
            #
            query=query,
            scroll=scroll,
            #
            doc_type=doc_type,
            index=index,
        )
