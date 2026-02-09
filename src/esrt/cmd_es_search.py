import typing as t

from pydantic import JsonValue

from .cmd_base import SimpleQueryCmd
from .typealiases import JsonBodyT


class EsSearchCmd(SimpleQueryCmd):
    _status_message: t.ClassVar[str] = 'Search ...'

    def _execute_query(self, body: t.Optional[JsonBodyT]) -> JsonValue:
        return self.client.search(
            index=self.index,
            doc_type=self.doc_type,
            body=body,
            params=self.params,
        )
