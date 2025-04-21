from pydantic import AliasChoices
from pydantic import Field
from pydantic_settings import CliImplicitFlag

from .cmd_base import BaseEsCmd
from .cmd_base import IpythonCmdMixin
from .cmd_base import VerboseCmdMixin
from .cmd_base import console
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console


class EsInfoCmd(
    IpythonCmdMixin,
    VerboseCmdMixin,
    BaseEsCmd,
):
    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_dim_console.out(f'Ping {self.client.hosts}')

        with stderr_console.status('Info ...') as _status:
            _status.update(spinner='bouncingBall')

            info = self.client.info()

            console.print_json(data=info)

        return self.start_ipython_if_need()
