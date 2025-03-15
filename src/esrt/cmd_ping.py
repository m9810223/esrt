from pydantic import AliasChoices
from pydantic import Field
from pydantic_settings import CliImplicitFlag

from .cmd_base import BaseCmd
from .cmd_base import console
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console


class PingCmd(BaseCmd):
    info: CliImplicitFlag[bool] = Field(
        default=True,
        validation_alias=AliasChoices(
            'info',
        ),
    )

    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_dim_console.print(f'Ping {self.client.hosts}')

        if not self.client.ping():
            stderr_console.print('Ping failed', style='red b')
            return

        stderr_console.print('Ping ok', style='green b')
        if self.info:
            console.print(self.client.info())
