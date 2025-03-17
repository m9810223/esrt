from collections import deque
import typing as t

from pydantic import AliasChoices
from pydantic import BeforeValidator
from pydantic import Field
from pydantic import validate_call
from pydantic_settings import CliImplicitFlag
from rich.text import Text
from uvicorn.importer import import_from_string

from .cmd_base import BaseEsCmd
from .cmd_base import ConfirmCmdMixin
from .cmd_base import DefaultNoPrettyCmdMixin
from .cmd_base import DryRunCmdMixin
from .cmd_base import EsDocTypeCmdMixin
from .cmd_base import EsIndexCmdMixin
from .cmd_base import EsParamsCmdMixin
from .cmd_base import IpythonCmdMixin
from .cmd_base import RequiredNdJsonInputCmdMixin
from .cmd_base import rich_text
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console
from .handlers import HandlerT
from .typealiases import JsonActionT


class BulkCmd(
    IpythonCmdMixin,
    ConfirmCmdMixin,
    RequiredNdJsonInputCmdMixin,
    EsIndexCmdMixin,
    EsDocTypeCmdMixin,
    EsParamsCmdMixin,
    DryRunCmdMixin,
    DefaultNoPrettyCmdMixin,
    BaseEsCmd,
):
    handler: t.Annotated[HandlerT, BeforeValidator(import_from_string)] = Field(
        default=t.cast(HandlerT, 'esrt:handle'),
        validation_alias=AliasChoices(
            'w',
            'handler',
        ),
        description=rich_text(Text('A callable handles actions.', style='blue b')),
    )

    chunk_size: int = Field(
        default=2000,
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

    def _check(self) -> bool:
        with stderr_console.status('Ping ...') as status:
            status.update(spinner='bouncingBall')

            p = self.client.ping()

        if p is True:
            return True

        stderr_console.print('Cannot connect to ES', style='red b')
        return False

    @validate_call(validate_return=True)
    def _generate_actions(self) -> t.Generator[JsonActionT, None, None]:
        iterator = self.handler(self.read_iterator_input())

        with self.progress(console=stderr_console, title='bulk') as progress:
            for action in progress.track(iterator):
                action.pop('_score', None)
                action.pop('sort', None)
                yield action

                if self.verbose:
                    if self.pretty:
                        self.output.print_json(data=action)
                    else:
                        self.output.print_json(data=action, indent=None)

                    progress.refresh()

    def _simulate(self, *, actions: t.Iterable[JsonActionT]) -> None:
        stderr_console.print('Dry run', style='yellow b')
        deque(actions, maxlen=0)
        stderr_console.print('Dry run end', style='yellow b')

    def cli_cmd(self) -> None:
        if (not self.dry_run) and (not self.confirm()):
            return

        if not self._check():
            return

        _actions = self._generate_actions()

        if self.dry_run:
            self._simulate(actions=_actions)
            return

        if not self.params:
            self.params = {
                'timeout': '1s',
            }

        for _, item in self.client.streaming_bulk(
            actions=_actions,
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
            if self.pretty:
                stderr_dim_console.print_json(data=item)
            else:
                stderr_dim_console.print_json(data=item, indent=None)

        if self.ipython:
            self.start_ipython()
