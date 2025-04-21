import contextlib
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
from .cmd_es_bulk import EsBulkCmd
from .cmd_es_info import EsInfoCmd
from .cmd_es_ping import EsPingCmd
from .cmd_es_request import EsRequestCmd
from .cmd_es_scan import EsScanCmd
from .cmd_es_search import EsSearchCmd
from .cmd_es_sql import EsSqlCmd
from .handlers import add_cwd_to_sys_path


class EsCmd(BaseSettings):
    # TODO: Add a description
    """
    The help text from the class docstring.
    """

    request: CliSubCommand[EsRequestCmd]
    sql: CliSubCommand[EsSqlCmd]

    ping: CliSubCommand[EsPingCmd]
    info: CliSubCommand[EsInfoCmd]
    search: CliSubCommand[EsSearchCmd]
    scan: CliSubCommand[EsScanCmd]
    bulk: CliSubCommand[EsBulkCmd]

    def cli_cmd(self) -> None:
        CliApp.run_subcommand(self)


class MainCmd(BaseSettings):
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

    es: CliSubCommand[EsCmd]

    def cli_cmd(self) -> None:
        if self.version is True:
            console.out(VERSION)
            return

        CliApp.run_subcommand(self)


def main() -> None:
    add_cwd_to_sys_path()
    try:
        with contextlib.suppress(KeyboardInterrupt):
            CliApp.run(MainCmd)
    except Exception as e:  # noqa: BLE001
        stderr_console.rule('exc_info', style='b yellow')
        stderr_console.out(traceback.format_exc().strip(), style='b i')
        stderr_console.rule('Exception', style='b red')
        stderr_console.print(e, style='b red')

        sys.exit(1)
