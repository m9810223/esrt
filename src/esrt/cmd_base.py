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
from rich.text import Text

from .clients import Client
from .typealiases import BodyT


console = Console()
stderr_console = Console(stderr=True)
stderr_dim_console = Console(stderr=True, style='dim')


body_ta = TypeAdapter[BodyT](Json[BodyT])


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def _validate_read(file: str) -> BodyT:
    to = t.cast('io.TextIOWrapper', sys.stdin) if file == '-' else Path(file).open()
    return body_ta.validate_python(to.read())


Input = t.Annotated[BodyT, PlainValidator(_validate_read)]


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def _validate_write(file_or_to: t.Union[str, io.TextIOWrapper]) -> io.TextIOWrapper:
    return Path(file_or_to).open('w') if isinstance(file_or_to, str) else file_or_to


Output = t.Annotated[io.TextIOWrapper, PlainValidator(_validate_write)]


def generate_rich_text(*objects: t.Any, sep: str = ' ', end: str = '\n') -> str:  # noqa: ANN401
    file = io.StringIO()
    record_console = Console(file=file, record=True)
    record_console.print(*objects, sep=sep, end=end)
    return record_console.export_text(styles=True)


class BaseCmd(BaseSettings):
    dry_run: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'n',
            'dry_run',
        ),
    )
    verbose: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'v',
            'verbose',
        ),
    )

    client: t.Annotated[Client, BeforeValidator(Client)] = Field(
        default=t.cast('Client', '127.0.0.1:9200'),
        validation_alias=AliasChoices(
            'host',
        ),
    )

    @staticmethod
    @validate_call(validate_return=True)
    def _json_obj_to_line(obj: JsonValue, /) -> str:
        if isinstance(obj, str):
            result = obj
        else:
            result = json.dumps(obj, ensure_ascii=False)

        if not result.endswith('\n'):
            return result + '\n'

        return result


class FioCmdMixin(BaseCmd):
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
    output: Output = Field(
        default=t.cast('Output', sys.stdout),
        validation_alias=AliasChoices(
            'o',
            'output',
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
            Text('A comma-separated list of index names to search;', style='blue b'),
            Text('use `_all` or empty string to perform the operation on all indices', style='blue b'),
        ),
    )


class DocTypeCmdMixin(BaseCmd):
    doc_type: t.Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            't',
            'doc-type',
            'doc_type',
        ),
        description=generate_rich_text(
            Text('A comma-separated list of document types to search;', style='blue b'),
            Text('leave empty to perform the operation on all types', style='blue b'),
        ),
    )


class ParamsCmdMixin(BaseCmd):
    params: dict[str, Json[JsonValue]] = Field(
        default_factory=dict,
        validation_alias=AliasChoices(
            'p',
            'param',
            'parameter',
        ),
        description=generate_rich_text(
            Text("""example: '--param=size=10 --param=_source=false'""", style='yellow b'),
            Text('Additional parameters to pass to the query', style='blue b'),
        ),
    )
