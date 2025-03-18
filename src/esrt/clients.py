import typing as t

from elasticsearch import Elasticsearch
from elasticsearch.helpers import expand_action
from elasticsearch.helpers import scan
from elasticsearch.helpers import streaming_bulk
from pydantic import JsonValue
from pydantic import validate_call

from .typealiases import HttpMethod
from .typealiases import JsonBodyT


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
        body: t.Optional[JsonBodyT] = None,
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
        query: t.Optional[JsonBodyT],
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

    @validate_call(validate_return=True)
    def streaming_bulk(  # noqa: PLR0913
        self,
        *,
        actions: t.Iterable[t.Union[str, bytes, dict[str, JsonValue]]],
        chunk_size: int,
        max_chunk_bytes: int,
        raise_on_error: bool,
        raise_on_exception: bool,
        max_retries: int,
        initial_backoff: int,
        max_backoff: int,
        yield_ok: bool,
        index: t.Optional[str],
        doc_type: t.Optional[str],
        params: dict[str, JsonValue],
        request_timeout: t.Optional[float],
    ) -> t.Generator[tuple[bool, dict[str, JsonValue]], None, None]:
        return streaming_bulk(
            client=self._client,
            actions=actions,
            chunk_size=chunk_size,
            max_chunk_bytes=max_chunk_bytes,
            raise_on_error=raise_on_error,
            raise_on_exception=raise_on_exception,
            expand_action_callback=expand_action,
            max_retries=max_retries,
            initial_backoff=initial_backoff,
            max_backoff=max_backoff,
            yield_ok=yield_ok,
            #
            index=index,
            doc_type=doc_type,
            params=params,
            request_timeout=request_timeout,
        )

    @validate_call(validate_return=True)
    def request(
        self,
        method: HttpMethod,
        url: str,
        headers: dict,
        params: dict,
        body: t.Optional[JsonBodyT],
    ) -> JsonValue:
        return self._client.transport.perform_request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            body=body,
        )
