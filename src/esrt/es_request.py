import sys
import typing as t
from urllib.parse import quote

import typer

from . import cli_params
from . import es
from .utils import json_obj_to_line
from .utils import merge_dicts


def es_request(
    host: t.Annotated[str, cli_params.host],
    finput_body: t.Optional[t.Annotated[typer.FileText, cli_params.input_file]] = None,
    foutput: t.Annotated[typer.FileTextWrite, cli_params.output_file] = t.cast(typer.FileTextWrite, sys.stdout),
    params: t.Annotated[t.Optional[list[dict]], cli_params.query_param] = None,
    headers: t.Annotated[t.Optional[list[dict]], cli_params.http_header] = None,
    #
    method: t.Annotated[str, typer.Option('-X', '--request', '--method', metavar='HTTP_METHOD', parser=str.upper, help='HTTP method')] = 'GET',
    url: t.Annotated[str, typer.Argument(metavar='URL_PATH', help='HTTP path')] = '/',
    quote_url: t.Annotated[bool, typer.Option('-Q', '--quote-url', help='Encode path with urllib.parse.quote but keep `,` and `*`')] = False,
    #
):
    client = es.Client(host=host)
    if not url.startswith('/'):
        url = '/' + url
    if quote_url:
        url = quote(string=url, safe=',*')
    response = client.transport.perform_request(
        method=method,
        url=url,
        headers=merge_dicts(headers),
        params=merge_dicts(params),
        body=finput_body and finput_body.read(),
    )
    foutput.write(json_obj_to_line(response))
