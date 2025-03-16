from contextlib import redirect_stdout
import sys
import typing as t

from elasticsearch import __versionstr__ as es_version
from pydantic import AliasChoices
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import CliApp
from pydantic_settings import CliImplicitFlag
from pydantic_settings import CliSubCommand
from pydantic_settings import SettingsConfigDict
from rich.console import Console
import typer
from typer.core import TyperGroup

from . import exceptions
from .__version__ import VERSION
from ._cli_help import Help
from ._cli_mixins import AliasGroupMixin
from ._cli_mixins import OrderGroupMixin
from ._es_bulk import es_bulk
from ._es_request import es_request
from ._es_scan import es_scan
from ._es_search import es_search
from ._es_sql import es_sql
from .handlers import add_cwd_to_sys_path
from .logging_ import logger
from .logging_ import set_log_level


console = Console()
stderr_console = Console(stderr=True)


class MyTyperGroup(AliasGroupMixin, OrderGroupMixin, TyperGroup):
    pass


app = typer.Typer(
    cls=MyTyperGroup,
    add_completion=False,
    no_args_is_help=True,
    context_settings={'help_option_names': ['-h', '--help']},
    help=' '.join(
        [
            typer.style(f'esrt v{VERSION}', fg=typer.colors.BRIGHT_CYAN, bold=True),
            typer.style(f'CLI use Python Elasticsearch=={es_version}', fg=typer.colors.BLACK, bold=True),
        ]
    ),
    pretty_exceptions_enable=False,
)
app.command(name='e / search', no_args_is_help=True, short_help=Help.e_search)(es_search)
app.command(name='s / scan / scroll', no_args_is_help=True, short_help=Help.s_scan)(es_scan)
app.command(name='r / request / api', no_args_is_help=True, short_help=Help.r_request)(es_request)
app.command(name='t / transmit / bulk', no_args_is_help=True, short_help=Help.t_transmit)(es_bulk)
app.command(name='sql', no_args_is_help=True, short_help=Help.sql)(es_sql)


@app.callback()
def log_level_cb(
    log_level: t.Annotated[
        str,
        typer.Option(
            '-l',
            '--log-level',
            envvar='ESRT_LOG_LEVEL',
            parser=str.upper,
            help='[ debug | info | warn | error | critical ]',
        ),
    ] = 'warning',
):
    set_log_level(log_level)
    logger.info(f'Log level: {log_level}')


class SearchCmd(BaseSettings):
    dry_run: CliImplicitFlag[bool] = Field(default=False)

    def cli_cmd(self) -> None:
        print(f'{self=}')


class MainCmd(BaseSettings):
    """
    The help text from the class docstring.
    """

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix='ESRT_',
        cli_prog_name='esrt',
        cli_enforce_required=True,
        cli_kebab_case=False,
    )

    version: CliImplicitFlag[bool] = Field(
        default=False,
        validation_alias=AliasChoices(
            'V',
            'version',
        ),
    )

    search: CliSubCommand[SearchCmd]

    def print_version(self) -> None:
        console.out(VERSION)

    def cli_cmd(self) -> None:
        logger.debug(self)

        if self.version is True:
            self.print_version()
            return

        CliApp.run_subcommand(self)


def main():
    add_cwd_to_sys_path()
    try:
        logger.info('CLI started')
        CliApp.run(MainCmd)
        app()
    except exceptions.TransportError as e:
        with redirect_stdout(sys.stderr):
            print(typer.style(e.info, dim=True))  # long
            print(typer.style(e, fg='yellow'))  # short
        sys.exit(1)
    except Exception as e:
        with redirect_stdout(sys.stderr):
            print(e)
        sys.exit(1)
