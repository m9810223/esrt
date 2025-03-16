from uvicorn.importer import import_from_string
import io
import json
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
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TaskProgressColumn
from rich.progress import TextColumn
from rich.progress import TimeElapsedColumn
from rich.progress import TimeRemainingColumn
from rich.text import Text

from .clients import Client
from .typealiases import BodyT


console = Console()
stderr_console = Console(stderr=True)
stderr_dim_console = Console(stderr=True, style='dim')


_T = t.TypeVar('_T')


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


_HandlerT = t.Callable[[t.Iterable[str]], t.Iterable[str]]


@validate_call(validate_return=True)
def _validate_handler(import_str: str) -> _HandlerT:
    return import_from_string(import_str)


Handler = t.Annotated[_HandlerT, PlainValidator(_validate_handler)]


def generate_rich_text(*objects: t.Any, sep: str = ' ', end: str = '\n') -> str:  # noqa: ANN401
    file = io.StringIO()
    record_console = Console(file=file, record=True)
    record_console.print(*objects, sep=sep, end=end)
    return record_console.export_text(styles=True)


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
    def _with_progress(
        self, iterable: t.Union[t.Iterable[_T], t.Sequence[_T]], /, *, console: Console, text: str
    ) -> t.Generator[_T, None, None]:
        with Progress(
            SpinnerColumn(),
            TextColumn(text_format=text),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            yield from progress.track(sequence=iterable)


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
        return self.output.file == sys.stdout


class SearchFioCmdMixin(_FileOutputCmdMixin):
    input_: t.Optional[Input] = Field(
        default=None,
        validation_alias=AliasChoices(
            'f',
            'input',
        ),
        description=generate_rich_text(
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
        description=generate_rich_text(
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
        description=generate_rich_text(
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
        description=generate_rich_text(
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
        description=generate_rich_text(
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
