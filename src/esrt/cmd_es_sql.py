import typing as t

from pydantic import AfterValidator
from pydantic import AliasChoices
from pydantic import Field

from .cmd_base import BaseEsCmd
from .cmd_base import DefaultPrettyCmdMixin
from .cmd_base import EsHeadersCmdMixin
from .cmd_base import EsParamsCmdMixin
from .cmd_base import IpythonCmdMixin
from .cmd_base import OutputCmdMixin
from .cmd_base import RequiredInputCmdMixin
from .cmd_base import VerboseCmdMixin
from .cmd_base import rich_text
from .cmd_base import stderr_console


def _validate_url(value: str) -> str:
    if not value.startswith('/'):
        value = f'/{value}'
    return value


class EsSqlCmd(
    EsHeadersCmdMixin,
    EsParamsCmdMixin,
    RequiredInputCmdMixin,
    DefaultPrettyCmdMixin,
    OutputCmdMixin,
    IpythonCmdMixin,
    VerboseCmdMixin,
    BaseEsCmd,
):
    sql_url: t.Annotated[str, AfterValidator(_validate_url)] = Field(
        default='/_sql',
        validation_alias=AliasChoices(
            'u',
            'sql_url',
        ),
        description=rich_text('[b blue]SQL API URL, e.g. `/_sql`, `/_xpack/sql`, `/_nlpcn/sql`, ...'),
    )

    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_console.print(self)

        with stderr_console.status('Request ...') as _status:
            _status.update(spinner='bouncingBall')

            response = self.client.request(
                method='GET',
                url=self.sql_url,
                headers=self.headers,
                params=self.params,
                body=self.read_input().strip(),
            )

        if isinstance(response, str):
            self.output.out(response)
            return self.start_ipython_if_need()

        if self.pretty:
            self.output.print_json(data=response)
        else:
            self.output.print_json(data=response, indent=None)

        return self.start_ipython_if_need()
