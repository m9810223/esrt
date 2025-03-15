import sys
import traceback

from pydantic import AliasChoices
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import CliApp
from pydantic_settings import CliImplicitFlag
from pydantic_settings import CliSubCommand
from pydantic_settings import SettingsConfigDict

from .__version__ import VERSION
from .cmd_base import console
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console
from .cmd_ping import PingCmd
from .cmd_scan import ScanCmd
from .cmd_search import SearchCmd


class MainCmd(BaseSettings):
    # TODO: Add a description
    """
    The help text from the class docstring.
    """

    model_config = SettingsConfigDict(
        case_sensitive=True,
        # env_prefix='ESRT_',
        cli_prog_name='esrt',
        cli_enforce_required=True,
        # cli_kebab_case=True,  # default is False
    )

    version: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'V',
            'version',
        ),
    )

    ping: CliSubCommand[PingCmd]
    search: CliSubCommand[SearchCmd]
    scan: CliSubCommand[ScanCmd]

    def cli_cmd(self) -> None:
        if self.version is True:
            console.out(VERSION)
            return

        CliApp.run_subcommand(self)


def main() -> None:
    try:
        CliApp.run(MainCmd)
    except Exception as e:  # noqa: BLE001
        stderr_dim_console.out(traceback.format_exc())
        stderr_console.out('Error:', e)
        sys.exit(1)
