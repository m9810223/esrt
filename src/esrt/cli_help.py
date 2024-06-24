from enum import Enum

import typer


class StrEnum(str, Enum): ...


class Command(StrEnum):
    search = 'search'
    scan = 'scan'
    request = 'request'
    transmit = 'transmit'

    sql = 'sql'

    @classmethod
    def width(cls):
        return len(max(cls.__members__.keys()))


class Help:
    _width = Command.width() + 1
    _fmt = f'{{:{_width}}}'

    e_search = typer.style(
        typer.style(_fmt.format(Command.search), fg=typer.colors.MAGENTA, bold=True)
        + typer.style('Elasticsearch.search', bold=True, dim=True, italic=True),
    )
    s_scan = typer.style(
        typer.style(_fmt.format(Command.scan), fg=typer.colors.MAGENTA, bold=True)
        + typer.style('helpers.scan', bold=True, dim=True, italic=True)
    )
    r_request = typer.style(
        typer.style(_fmt.format(Command.request), fg=typer.colors.MAGENTA, bold=True)
        + typer.style('Transport.perform_request', bold=True, dim=True, italic=True),
    )
    t_transmit = typer.style(
        typer.style(_fmt.format(Command.transmit), fg=typer.colors.MAGENTA, bold=True)
        + typer.style('helpers.streaming_bulk', bold=True, dim=True, italic=True)
    )

    sql = typer.style(
        typer.style(_fmt.format(Command.sql), fg=typer.colors.MAGENTA, bold=True)
        + typer.style('request -X POST /_sql', bold=True, dim=True, italic=True),
    )
