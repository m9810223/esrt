import io
import json
import os
from pathlib import Path
import sys
import typing as t

from pydantic import AliasChoices
from pydantic import BeforeValidator
from pydantic import ConfigDict
from pydantic import Field
from pydantic import Json
from pydantic import JsonValue
from pydantic import PlainValidator
from pydantic import TypeAdapter
from pydantic import validate_call
from pydantic_settings import BaseSettings
from pydantic_settings import CliImplicitFlag
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

from .clients import Client
from .typealiases import BodyT


console = Console()
stderr_console = Console(stderr=True)
stderr_dim_console = Console(stderr=True, style='dim')


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def _validate_output(file_or_to: t.Union[str, io.TextIOWrapper]) -> Console:
    file = Path(file_or_to).open('w') if isinstance(file_or_to, str) else file_or_to  # noqa: SIM115
    return Console(file=file)


Output = t.Annotated[Console, PlainValidator(_validate_output)]


_body_ta = TypeAdapter[BodyT](Json[BodyT])


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def _validate_input(file: str) -> BodyT:
    tio = t.cast('io.TextIOWrapper', sys.stdin) if file == '-' else Path(file).open()  # noqa: SIM115
    return _body_ta.validate_python(tio.read())


Input = t.Annotated[BodyT, PlainValidator(_validate_input)]


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def _validate_input_file(file_or_to: t.Union[str, io.TextIOWrapper]) -> io.TextIOWrapper:
    file = Path(file_or_to).open('r') if isinstance(file_or_to, str) else file_or_to  # noqa: SIM115
    return file


ReadFile = t.Annotated[io.TextIOWrapper, PlainValidator(_validate_input_file)]


def rich_text(*objects: t.Any, sep: str = ' ', end: str = '\n') -> str:  # noqa: ANN401
    """Return a string representation of the object, formatted with rich text."""
    file = io.StringIO()
    record_console = Console(file=file, record=True)
    record_console.print(*objects, sep=sep, end=end)
    return record_console.export_text(styles=True)


class _TransferSpeedColumn(TransferSpeedColumn):
    def render(self, task: 'Task') -> Text:
        """Show data transfer speed."""
        speed = task.finished_speed or task.speed
        if speed is None:
            return Text('?', style='progress.data.speed')
        data_speed = int(speed)
        return Text(f'{data_speed}/s', style='progress.data.speed')


class BaseCmd(BaseSettings):
    client: t.Annotated[Client, BeforeValidator(Client)] = Field(
        default=t.cast('Client', '127.0.0.1:9200'),
        validation_alias=AliasChoices(
            'H',
            'host',
        ),
    )
    verbose: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'v',
            'verbose',
        ),
    )

    @staticmethod
    @validate_call(validate_return=True)
    def _to_json_str(obj: JsonValue, /) -> str:
        return json.dumps(obj)

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
    def _progress(self, *, console: Console, title: str) -> Progress:
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

    def _tty_confirm(self, prompt: str, /, *, default: t.Optional[bool] = None) -> bool:
        tty = Path(os.ctermid())
        return Confirm.ask(
            prompt=prompt,
            console=Console(file=tty.open('r+')),
            default=t.cast('bool', default),  # ! type bug in rich
            stream=tty.open('r'),
        )


class _FileOutputCmdMixin(BaseCmd):
    output: Output = Field(
        default=t.cast('Output', sys.stdout),
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


class SearchFioCmdMixin(_FileOutputCmdMixin):
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


class BulkFioCmdMixin(_FileOutputCmdMixin):
    input_: ReadFile = Field(
        default=t.cast('ReadFile', sys.stdin),
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


class IndexCmdMixin(BaseCmd):
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


class DocTypeCmdMixin(BaseCmd):
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


class ParamsCmdMixin(BaseCmd):
    params: dict[str, JsonValue] = Field(
        default_factory=dict,
        validation_alias=AliasChoices(
            'p',
            'param',
        ),
        description=rich_text(
            Text("""example: '--param=size=10 --param=_source=false'""", style='yellow b'),
            Text('Additional parameters to pass to the query', style='blue b'),
        ),
    )


class DryRunCmdMixin(BaseCmd):
    dry_run: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'n',
            'dry_run',
        ),
    )


class PrettyCmdMixin(BaseCmd):
    pretty: CliImplicitFlag[bool] = True


class NotPrettyCmdMixin(BaseCmd):
    pretty: CliImplicitFlag[bool] = False
