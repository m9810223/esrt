import typing as t

from pydantic import AfterValidator
from pydantic import AliasChoices
from pydantic import BeforeValidator
from pydantic import Field
from rich.text import Text

from .cmd_base import BaseEsCmd
from .cmd_base import DefaultPrettyCmdMixin
from .cmd_base import EsHeadersCmdMixin
from .cmd_base import EsParamsCmdMixin
from .cmd_base import IpythonCmdMixin
from .cmd_base import JsonInputCmdMixin
from .cmd_base import rich_text
from .cmd_base import stderr_console
from .typealiases import HttpMethod


def _validate_url(value: str) -> str:
    if not value.startswith('/'):
        value = f'/{value}'
    return value


class RequestCmd(
    IpythonCmdMixin,
    JsonInputCmdMixin,
    EsHeadersCmdMixin,
    EsParamsCmdMixin,
    DefaultPrettyCmdMixin,
    BaseEsCmd,
):
    method: t.Annotated[HttpMethod, BeforeValidator(str.upper)] = Field(
        default='GET',
        validation_alias=AliasChoices(
            'X',
            'method',
            'request',
        ),
    )
    url: t.Annotated[str, AfterValidator(_validate_url)] = Field(
        default='/',
        validation_alias=AliasChoices(
            'u',
            'url',
        ),
        description=rich_text(
            Text('Absolute url (without host) to target', style='blue b'),
        ),
    )

    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_console.print(self)

        with stderr_console.status('Request ...') as status:
            status.update(spinner='bouncingBall')

            response = self.client.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                params=self.params,
                body=self.read_json_input(),
            )

        if isinstance(response, str):
            self.output.out(response)
            return

        s = self.json_to_str(response)

        if self.pretty:
            self.output.print_json(s)
        else:
            self.output.print_json(s, indent=None)

        if self.ipython:
            self.start_ipython()
