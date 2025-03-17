import inspect
import io
import json
import os
from pathlib import Path
import sys
import typing as t

import IPython
from pydantic import AliasChoices
from pydantic import BeforeValidator
from pydantic import ConfigDict
from pydantic import Field
from pydantic import Json
from pydantic import JsonValue
from pydantic import PlainValidator
from pydantic import TypeAdapter
from pydantic import model_validator
from pydantic import validate_call
from pydantic_settings import BaseSettings
from pydantic_settings import CliImplicitFlag
from pydantic_settings import CliPositionalArg
from rich.console import Console
from rich.progress import BarColumn
from rich.progress import MofNCompleteColumn
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import Task
from rich.progress import TaskProgressColumn
from rich.progress import TextColumn
from rich.progress import TimeElapsedColumn
from rich.progress import TimeRemainingColumn
from rich.progress import TotalFileSizeColumn
from rich.progress import TransferSpeedColumn
from rich.prompt import Confirm
from rich.text import Text
from typing_extensions import Self

from .clients import Client
from .typealiases import JsonBodyT


console = Console()
stderr_console = Console(stderr=True)
stderr_dim_console = Console(stderr=True, style='dim')


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def _validate_output_console(file_or_tio: t.Union[str, io.TextIOWrapper]) -> Console:
    tio = Path(file_or_tio).open('w') if isinstance(file_or_tio, str) else file_or_tio  # noqa: SIM115
    return Console(file=tio)


OutputConsole = t.Annotated[Console, PlainValidator(_validate_output_console)]


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def _validate_input_file(file_or_tio: t.Union[str, io.TextIOWrapper]) -> io.TextIOWrapper:
    tio = (
        (t.cast(io.TextIOWrapper, sys.stdin) if file_or_tio == '-' else Path(file_or_tio).open('r'))  # noqa: SIM115
        if isinstance(file_or_tio, str)
        else file_or_tio
    )
    return tio


Input = t.Annotated[io.TextIOWrapper, PlainValidator(_validate_input_file)]


json_body_type_adapter = TypeAdapter[JsonBodyT](Json[JsonBodyT])


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def _validate_json_input(file: str) -> t.Optional[JsonBodyT]:
    tio = t.cast(io.TextIOWrapper, sys.stdin) if file == '-' else Path(file).open('r')  # noqa: SIM115
    s = tio.read().strip() or None
    return None if s is None else json_body_type_adapter.validate_python(s)


JsonInput = t.Annotated[JsonBodyT, PlainValidator(_validate_json_input)]


def rich_text(*objects: t.Any, sep: str = ' ', end: str = '\n') -> str:  # noqa: ANN401
    """Return a string representation of the object, formatted with rich text."""
    file = io.StringIO()
    record_console = Console(file=file, record=True)
    record_console.print(*objects, sep=sep, end=end)  # color
    return record_console.export_text(styles=True)


class _TransferSpeedColumn(TransferSpeedColumn):
    def render(self, task: 'Task') -> Text:
        """Show data transfer speed."""
        speed = task.finished_speed or task.speed
        if speed is None:
            return Text('?', style='progress.data.speed')
        data_speed = int(speed)
        return Text(f'{data_speed}/s', style='progress.data.speed')


class _BaseCmd(BaseSettings):
    verbose: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'v',
            'verbose',
        ),
    )

    output: OutputConsole = Field(
        default=t.cast(OutputConsole, sys.stdout),
        validation_alias=AliasChoices(
            'o',
            'output',
        ),
    )

    @property
    def is_output_stdout(self) -> bool:
        return self.output.file in [
            sys.stdout,
            getattr(sys.stdout, 'rich_proxied_file', None),  # * rich.progress.Progress
        ]

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
    def progress(self, *, console: Console, title: str) -> Progress:
        return Progress(
            SpinnerColumn(),
            TextColumn(text_format=title),
            BarColumn(),
            TimeElapsedColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            TotalFileSizeColumn(),
            MofNCompleteColumn(),
            _TransferSpeedColumn(),
            console=console,
        )

    @staticmethod
    @validate_call(validate_return=True)
    def json_to_str(obj: JsonValue, /) -> str:
        return json.dumps(obj)

    @staticmethod
    def _tty_confirm(prompt: str, /, *, default: t.Optional[bool] = None) -> bool:
        tty = Path(os.ctermid())
        return Confirm.ask(
            prompt=prompt,
            console=Console(file=tty.open('r+')),
            default=t.cast(bool, default),  # ! type bug in rich
            stream=tty.open('r'),
        )


class ConfirmCmdMixin(_BaseCmd):
    yes: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'y',
            'yes',
        ),
        description=rich_text(Text('Do not ask for confirmation', style='blue b')),
    )

    def confirm(self) -> bool:
        if self.yes is True:
            if self.verbose is True:
                stderr_dim_console.print(self)
            return True

        confirm = self._tty_confirm(rich_text(self, 'Continue?', end=''))
        if confirm is True:
            return True

        stderr_console.print('Aborted!', style='red b')
        return False


class IpythonCmdMixin(_BaseCmd):
    ipython: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'ipy',
            'ipython',
        ),
    )

    def _print_user_ns(self, target_ns: dict[str, t.Any], /) -> None:
        stderr_console.print()
        stderr_console.print('variables:')
        for v in target_ns:
            if v.startswith('_'):
                continue
            stderr_console.print(f'* {v}', style='cyan b')

    @property
    def _stdin_is_a_tty(self) -> bool:
        """
        -f - (GOOD)
            sys.stdin.isatty() = True
            sys.stdin.seekable() = True
            color OK!
        |
            sys.stdin.isatty() = False
            sys.stdin.seekable() = False
            color GG!
        -f - <<<
            sys.stdin.isatty() = False
            sys.stdin.seekable() = True
            color GG!
        """
        if 0:
            stderr_console.print(f'{sys.stdin.isatty() = }')
            stderr_console.print(f'{sys.stdin.seekable() = }')
        return sys.stdin.isatty()

    def _replace_stdin(self) -> None:
        tty = Path(os.ctermid())
        sys.stdin = tty.open('r')

    def start_ipython(self) -> None:
        """
        Maybe replace sys.stdin with a tty file.
        """
        curr_frame = inspect.currentframe()
        assert curr_frame is not None

        target_frame = curr_frame.f_back
        assert target_frame is not None

        target_ns = target_frame.f_locals
        self._print_user_ns(target_ns)

        if not self._stdin_is_a_tty:
            self._replace_stdin()

        IPython.start_ipython(argv=[], user_ns=target_ns)


class BaseEsCmd(_BaseCmd):
    client: CliPositionalArg[t.Annotated[Client, BeforeValidator(Client)]] = Field(
        default=t.cast(Client, '127.0.0.1:9200'),
        validation_alias=AliasChoices(
            'es_host',
        ),
    )


class _BaseInputCmdMixin(_BaseCmd):
    input_: t.Optional[Input] = Field(
        default=None,
        validation_alias=AliasChoices(
            'f',
            'input',
        ),
        description=rich_text(
            Text('A file containing the search query.', style='blue b'),
            Text("""example: '-f my_query.txt'.""", style='yellow b'),
            Text("""Or '-f -' for stdin.""", style='yellow b'),
            Text('Exclusive with -d/--data.', style='red b'),
        ),
    )
    data: t.Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            'd',
            'data',
        ),
        description=rich_text(
            Text('A string containing the search query.', style='blue b'),
            Text('Exclusive with -f/--input.', style='red b'),
        ),
    )

    @property
    def is_input_stdin(self) -> bool:
        return self.input_ == sys.stdin

    def read_input(self) -> t.Optional[str]:
        if self.data is not None:
            return self.data

        if self.input_ is None:
            return None

        return self.input_.read()


class JsonInputCmdMixin(_BaseInputCmdMixin):
    @model_validator(mode='after')
    def _validate_input(self) -> Self:
        if (self.input_ is not None) and (self.data is not None):
            message = 'Only one of `-f/--input` or `-d/--data` is allowed.'
            raise ValueError(message)

        return self

    input_: t.Optional[Input] = Field(
        default=None,
        validation_alias=AliasChoices(
            'f',
            'input',
        ),
        description=rich_text(
            Text("""example: '-f my_query.json'.""", style='yellow b'),
            Text("""Or '-f -' for stdin.""", style='red b'),
            Text('A JSON file containing the search query.', style='blue b'),
        ),
    )

    def read_json_input(self) -> t.Optional[JsonBodyT]:
        if self.data is not None:
            if self.data == '':
                return None

            return json_body_type_adapter.validate_python(self.data)

        if self.input_ is None:
            return None

        if self.input_.seekable():
            self.input_.seek(0)

        x = self.input_.read()
        if x == '':
            return None

        return json_body_type_adapter.validate_python(x)


class RequiredNdJsonInputCmdMixin(_BaseInputCmdMixin):
    @model_validator(mode='after')
    def _validate_input(self) -> Self:
        if (self.input_ is None) and (self.data is None):
            self.input_ = t.cast(Input, sys.stdin)

        if (self.input_ is not None) and (self.data is not None):
            message = 'Only one of `-f/--input` or `-d/--data` is allowed.'
            raise ValueError(message)

        return self

    input_: t.Optional[Input] = Field(
        default=None,
        validation_alias=AliasChoices(
            'f',
            'input',
        ),
        description=rich_text(
            Text("""example: '-f my_query.ndjson'.""", style='yellow b'),
            Text("""Or '-f -' for stdin.""", style='red b'),
            Text('A NDJSON (Newline delimited JSON) file containing the bulk request.', style='blue b'),
        ),
    )

    def read_iterator_input(self) -> t.Iterable[str]:
        if self.data is not None:
            return self.data.strip().splitlines(keepends=True)

        assert self.input_ is not None

        if self.input_.seekable():
            self.input_.seek(0)

        return (x for x in self.input_ if x.strip())


class EsIndexCmdMixin(BaseEsCmd):
    index: t.Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            'i',
            'index',
        ),
        description=rich_text(
            Text("""example: '--index=i01,i02'""", style='yellow b'),
            Text(
                'A comma-separated list of index names to search; use `_all` or empty string to perform the operation on all indices',  # noqa: E501
                style='blue b',
            ),
        ),
    )


class EsDocTypeCmdMixin(BaseEsCmd):
    doc_type: t.Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            'doc_type',
        ),
        description=rich_text(
            Text(
                'A comma-separated list of document types to search; leave empty to perform the operation on all types',
                style='blue b',
            ),
        ),
    )


class EsHeadersCmdMixin(BaseEsCmd):
    headers: dict[str, JsonValue] = Field(
        default_factory=dict,
        validation_alias=AliasChoices(
            'H',
            'header',
        ),
        description=rich_text(
            Text("""example: '--header a=1 --header b=false'""", style='yellow b'),
            Text('Additional parameters to pass to the query', style='blue b'),
        ),
    )


class EsParamsCmdMixin(BaseEsCmd):
    params: dict[str, JsonValue] = Field(
        default_factory=dict,
        validation_alias=AliasChoices(
            'p',
            'param',
        ),
        description=rich_text(
            Text("""example: '--param a=1 --param b=false'""", style='yellow b'),
            Text('Additional parameters to pass to the query', style='blue b'),
        ),
    )


class DryRunCmdMixin(BaseEsCmd):
    dry_run: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'n',
            'dry_run',
        ),
    )


class DefaultPrettyCmdMixin(BaseEsCmd):
    pretty: CliImplicitFlag[bool] = Field(
        default=True,
    )


class DefaultNoPrettyCmdMixin(BaseEsCmd):
    pretty: CliImplicitFlag[bool] = Field(
        default=False,
    )
