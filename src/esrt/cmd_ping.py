from pydantic import AliasChoices
from pydantic import Field
from pydantic_settings import CliImplicitFlag

from .cmd_base import BaseEsCmd
from .cmd_base import console
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console


class PingCmd(BaseEsCmd):
    info: CliImplicitFlag[bool] = Field(
        default=True,
        validation_alias=AliasChoices(
            'I',
            'info',
        ),
    )

    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_dim_console.out(f'Ping {self.client.hosts}')

        if not self.client.ping():
            stderr_console.out('Ping failed', style='red b')
            return

        stderr_console.out('Ping ok', style='green b')
        if self.info:
            s = self.json_to_str(self.client.info())
            console.print_json(s)
