from collections import deque
import typing as t

from pydantic import AliasChoices
from pydantic import BeforeValidator
from pydantic import Field
from pydantic_settings import CliImplicitFlag
from rich.text import Text
from uvicorn.importer import import_from_string

from .cmd_base import BaseCmd
from .cmd_base import BulkFioCmdMixin
from .cmd_base import DocTypeCmdMixin
from .cmd_base import DryRunCmdMixin
from .cmd_base import IndexCmdMixin
from .cmd_base import NotPrettyCmdMixin
from .cmd_base import ParamsCmdMixin
from .cmd_base import rich_text
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console
from .typealiases import ActionT


_HandlerT = t.Annotated[t.Callable, BeforeValidator(import_from_string)]


class BulkCmd(
    BulkFioCmdMixin, IndexCmdMixin, DocTypeCmdMixin, ParamsCmdMixin, DryRunCmdMixin, NotPrettyCmdMixin, BaseCmd
):
    handler: _HandlerT = Field(
        default=t.cast('_HandlerT', 'esrt:DocHandler'),
        validation_alias=AliasChoices(
            'w',
            'handler',
        ),
        description=rich_text(Text('A callable handles actions.', style='blue b')),
    )

    chunk_size: int = Field(
        default=5000,
        validation_alias=AliasChoices(
            'c',
            'chunk_size',
        ),
        description=rich_text(Text('Number of docs in one chunk sent to es', style='blue b')),
    )
    max_chunk_bytes: int = Field(
        default=100 * 1024 * 1024,
        description=rich_text(Text('The maximum size of the request in bytes', style='blue b')),
    )
    raise_on_error: CliImplicitFlag[bool] = Field(
        default=True,
        description=rich_text(
            Text(
                """Raise `BulkIndexError` containing errors from the execution of the last chunk when some occur.""",
                style='blue b',
            )
        ),
    )
    raise_on_exception: CliImplicitFlag[bool] = Field(
        default=True,
        description=rich_text(
            Text(
                """If `False` then don't propagate exceptions from call to `bulk` and just report the items that failed as failed.""",  # noqa: E501
                style='blue b',
            )
        ),
    )
    max_retries: int = Field(
        default=5,
        description=rich_text(
            Text(
                'Maximum number of times a document will be retried when `429` is received, set to 0 for no retries on `429`',  # noqa: E501
                style='blue b',
            )
        ),
    )
    initial_backoff: int = Field(
        default=3,
        description=rich_text(
            Text(
                'Number of seconds we should wait before the first retry. Any subsequent retries will be powers of `initial_backoff * 2**retry_number`',  # noqa: E501
                style='blue b',
            )
        ),
    )
    max_backoff: int = Field(
        default=600,
        description=rich_text(
            Text(
                'Maximum number of seconds a retry will wait',
                style='blue b',
            )
        ),
    )
    yield_ok: CliImplicitFlag[bool] = Field(
        default=False,
        description=rich_text(
            Text(
                'If set to False will skip successful documents in the output',
                style='blue b',
            )
        ),
    )
    yes: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'y',
            'yes',
        ),
        description=rich_text(
            Text(
                'Do not ask for confirmation',
                style='blue b',
            )
        ),
    )

    def cli_cmd(self) -> None:  # noqa: C901
        if not self.yes:
            confirm = self._tty_confirm(rich_text(self, 'Continue?', end=''))
            if not confirm:
                stderr_console.print('Aborted', style='red b')
                return

        if self.client.ping() is False:
            stderr_console.print('Cannot connect to ES', style='red b')
            return

        inputs = t.cast('t.Callable[[t.Iterable[str]], t.Iterable[ActionT]]', self.handler)(self.input_)

        def generate_actions() -> t.Generator[ActionT, None, None]:
            with self._progress(console=stderr_console, title='bulk') as progress:
                for action in progress.track(inputs):
                    if isinstance(action, dict):
                        action.pop('_score', None)
                        action.pop('sort', None)
                    yield action

                    if self.verbose:
                        line = self._to_json_str(action)
                        if self.pretty:
                            self.output.print_json(line)
                        else:
                            self.output.out(action)
                        progress.refresh()

        actions = generate_actions()

        if self.dry_run:
            stderr_console.print('Dry run', style='yellow b')
            deque(actions, maxlen=0)
            stderr_console.print('Dry run end', style='yellow b')
            return

        pairs = self.client.streaming_bulk(
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
        )

        for _, item in pairs:
            line = self._to_json_str(item)
            stderr_dim_console.out(line)
