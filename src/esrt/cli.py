import sys
import typing as t

from elasticsearch import __versionstr__ as es_version
import typer
from typer.core import TyperGroup

from . import exceptions
from .__version__ import VERSION
from .cli_help import Help
from .cli_mixins import AliasGroupMixin
from .cli_mixins import OrderGroupMixin
from .es_bulk import es_bulk
from .es_request import es_request
from .es_scan import es_scan
from .es_search import es_search
from .es_sql import es_sql
from .handlers import insert_cwd
from .logger import logger
from .logger import set_log_level


class MyTyperGroup(AliasGroupMixin, OrderGroupMixin, TyperGroup):
    pass


app = typer.Typer(
    cls=MyTyperGroup,
    add_completion=False,
    no_args_is_help=True,
    #
    context_settings={'help_option_names': ['-h', '--help']},
    help=' '.join(
        [
            typer.style(f'esrt v{VERSION}', fg=typer.colors.BRIGHT_CYAN, bold=True),
            typer.style(f'CLI use Python Elasticsearch=={es_version}', fg=typer.colors.BLACK, bold=True),
        ]
    ),
    #
    pretty_exceptions_enable=False,
)
app.command(name='e / search', no_args_is_help=True, short_help=Help.e_search)(es_search)
app.command(name='s / scan / scroll', no_args_is_help=True, short_help=Help.s_scan)(es_scan)
app.command(name='r / request / api', no_args_is_help=True, short_help=Help.r_request)(es_request)
app.command(name='t / transmit / bulk', no_args_is_help=True, short_help=Help.t_transmit)(es_bulk)
app.command(name='sql', no_args_is_help=True, short_help=Help.sql)(es_sql)


@app.callback()
def log_level_cb(log_level: t.Annotated[str, typer.Option('-l', '--log-level', envvar='ESRT_LOG_LEVEL', parser=str.upper, help='[ debug | info | warn | error | critical ]')] = 'warn'):
    set_log_level(log_level)
    logger.info(f'Log level: {log_level}')


def main():
    insert_cwd()
    try:
        logger.info('CLI started')
        app()
    except exceptions.TransportError as e:
        print(typer.style(e.info, dim=True))  # long
        print(typer.style(e, fg='yellow'))  # short
        sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)
