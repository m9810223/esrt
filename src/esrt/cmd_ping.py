from .cmd_base import BaseCmd
from .cmd_base import console
from .cmd_base import stderr_dim_console


class PingCmd(BaseCmd):
    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_dim_console.print(f'Ping {self.client.hosts}')

        if self.client.ping():
            console.print('Ping OK')
        else:
            stderr_dim_console.print('Ping failed')
