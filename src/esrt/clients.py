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
        return self._client.search(
            index=index,
            doc_type=doc_type,
            body=body,
            params=params,
        )

    @validate_call(validate_return=True)
    def scan(  # noqa: PLR0913
        self,
        *,
        query: t.Optional[BodyT],
        scroll: str,
        raise_on_error: bool,
        preserve_order: bool,
        size: int,
        request_timeout: t.Optional[float],
        clear_scroll: bool,
        scroll_kwargs: dict[str, JsonValue],
        #
        index: t.Optional[str],
        doc_type: t.Optional[str],
        params: dict[str, JsonValue],
    ) -> t.Generator[dict[str, JsonValue], None, None]:
        return scan(
            client=self._client,
            #
            query=query,
            scroll=scroll,
            raise_on_error=raise_on_error,
            preserve_order=preserve_order,
            size=size,
            request_timeout=request_timeout,
            clear_scroll=clear_scroll,
            scroll_kwargs=scroll_kwargs,
            # [kwargs]
            doc_type=doc_type,
            index=index,
            **params,
        )
