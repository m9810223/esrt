from collections import deque
import typing as t

from pydantic import AliasChoices
from pydantic import Field
from pydantic import PlainValidator
from pydantic_settings import CliImplicitFlag
from rich.text import Text
from uvicorn.importer import import_from_string

from .cmd_base import BaseCmd
from .cmd_base import BulkFioCmdMixin
from .cmd_base import DocTypeCmdMixin
from .cmd_base import DryRunCmdMixin
from .cmd_base import IndexCmdMixin
from .cmd_base import ParamsCmdMixin
from .cmd_base import generate_rich_text
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console
from .typealiases import ActionT


_HandlerT = t.Annotated[t.Callable[[t.Iterable[t.Any]], t.Iterable[ActionT]], PlainValidator(import_from_string)]


class BulkCmd(BulkFioCmdMixin, IndexCmdMixin, DocTypeCmdMixin, ParamsCmdMixin, DryRunCmdMixin, BaseCmd):
    handler: _HandlerT = Field(
        default=t.cast('_HandlerT', 'esrt:DocHandler'),
        validation_alias=AliasChoices(
            'w',
            'handler',
        ),
        description=generate_rich_text(Text('A callable handles actions.', style='blue b')),
    )

    chunk_size: int = Field(
        default=500,
        validation_alias=AliasChoices(
            'c',
            'chunk_size',
        ),
        description=generate_rich_text(Text('Number of docs in one chunk sent to es', style='blue b')),
    )
    max_chunk_bytes: int = Field(
        default=100 * 1024 * 1024,
        description=generate_rich_text(Text('The maximum size of the request in bytes', style='blue b')),
    )
    raise_on_error: CliImplicitFlag[bool] = Field(
        default=True,
        description=generate_rich_text(
            Text(
                """Raise `BulkIndexError` containing errors from the execution of the last chunk when some occur.""",
                style='blue b',
            )
        ),
    )
    raise_on_exception: CliImplicitFlag[bool] = Field(
        default=True,
        description=generate_rich_text(
            Text(
                """If `False` then don't propagate exceptions from call to `bulk` and just report the items that failed as failed.""",  # noqa: E501
                style='blue b',
            )
        ),
    )
    max_retries: int = Field(
        default=0,
        description=generate_rich_text(
            Text(
                'Maximum number of times a document will be retried when `429` is received, set to 0 for no retries on `429`',  # noqa: E501
                style='blue b',
            )
        ),
    )
    initial_backoff: int = Field(
        default=2,
        description=generate_rich_text(
            Text(
                'Number of seconds we should wait before the first retry. Any subsequent retries will be powers of `initial_backoff * 2**retry_number`',  # noqa: E501
                style='blue b',
            )
        ),
    )
    max_backoff: int = Field(
        default=600,
        description=generate_rich_text(
            Text(
                'Maximum number of seconds a retry will wait',
                style='blue b',
            )
        ),
    )
    yield_ok: CliImplicitFlag[bool] = Field(
        default=False,
        description=generate_rich_text(
            Text(
                'If set to False will skip successful documents in the output',
                style='blue b',
            )
        ),
    )

    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_dim_console.print(self)

        if self.client.ping() is False:
            stderr_console.print('Cannot connect to ES', style='red b')
            return

        def generate_actions() -> t.Generator[ActionT, None, None]:
            with self._progress(console=stderr_console, title='bulk') as progress:
                for action in progress.track(self.handler(self.input_)):
                    if isinstance(action, dict):
                        action.pop('_score', None)
                        action.pop('sort', None)
                    yield action
                    line = self._to_json_str(action)
                    stderr_console.print_json(line, ensure_ascii=True)
                    progress.refresh()

        actions = generate_actions()

        if self.dry_run:
            stderr_console.print('Dry run', style='yellow b')
            deque(actions, maxlen=0)
            return

        for _, item in self.client.streaming_bulk(
            actions=actions,
            chunk_size=self.chunk_size,
            max_chunk_bytes=self.max_chunk_bytes,
            raise_on_error=self.raise_on_error,
            raise_on_exception=self.raise_on_exception,
            max_retries=self.max_retries,
            initial_backoff=self.initial_backoff,
            max_backoff=self.max_backoff,
            yield_ok=self.yield_ok,
            index=self.index,
            doc_type=self.doc_type,
            params=self.params,
        ):
            stderr_dim_console.print(item)
