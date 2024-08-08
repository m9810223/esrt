import sys
import typing as t

import typer

from . import cli_params
from .es_request import es_request


def es_sql(
    host: t.Annotated[str, cli_params.host],
    input_file: t.Annotated[typer.FileText, cli_params.input_file],
    output_file: t.Annotated[typer.FileTextWrite, cli_params.output_file] = t.cast(typer.FileTextWrite, sys.stdout),
    params: t.Annotated[t.Optional[list[dict]], cli_params.query_param] = None,
    headers: t.Annotated[t.Optional[list[dict]], cli_params.http_header] = None,
    #
    api: t.Annotated[str, typer.Option(envvar='ESRT_SQL_API', help='[ _sql | _xpack/sql | _nlpcn/sql | ... ]')] = '_sql',  # https://github.com/NLPchina/elasticsearch-sql
):
    if not api.startswith('/'):
        api = '/' + api
    return es_request(
        host=host,
        input_file=input_file,
        output_file=output_file,
        method='POST',  # *
        url=api,  # *
        params=params,
        headers=headers,
    )
