from .cmd_base import stderr_dim_console
import typing as t

from pydantic import AliasChoices
from pydantic_settings import CliImplicitFlag
from pydantic import Field
from rich.text import Text

from .cmd_base import BaseCmd
from .cmd_base import BulkFioCmdMixin
from .cmd_base import DocTypeCmdMixin
from .cmd_base import Handler
from .cmd_base import IndexCmdMixin
from .cmd_base import ParamsCmdMixin
from .cmd_base import generate_rich_text
from .cmd_base import stderr_console


class BulkCmd(BulkFioCmdMixin, IndexCmdMixin, DocTypeCmdMixin, ParamsCmdMixin, BaseCmd):
    handler: Handler = Field(
        default=t.cast('Handler', 'esrt:DocHandler'),
        validation_alias=AliasChoices(
            'i',
            'index',
        ),
        description=generate_rich_text(Text('A callable handles actions.', style='blue b')),
    )

    chunk_size: int = Field(
        default=500,
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
        default=True,
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

        for _, item in self._with_progress(
            self.client.streaming_bulk(
                actions=self.handler(self.input_),
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
            ),
            console=stderr_console,
            text='Processing...',
        ):
            line = self._to_json_str(item)

            self.output.out(line)
