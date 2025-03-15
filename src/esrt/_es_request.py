from pprint import pformat
import sys
import typing as t
from urllib.parse import quote

import typer

from . import _cli_params
from . import es
from .logging_ import logger
from .utils import json_obj_to_line
from .utils import merge_dicts


def es_request(
    host: t.Annotated[str, _cli_params.host],
    input_file: t.Annotated[t.Optional[typer.FileText], _cli_params.input_file] = None,
    output_file: t.Annotated[typer.FileTextWrite, _cli_params.output_file] = t.cast('typer.FileTextWrite', sys.stdout),
    query_param: t.Annotated[t.Optional[list[dict]], _cli_params.query_param] = None,
    http_header: t.Annotated[t.Optional[list[dict]], _cli_params.http_header] = None,
    method: t.Annotated[
        str, typer.Option('-X', '--request', '--method', metavar='HTTP_METHOD', parser=str.upper, help='HTTP method')
    ] = 'GET',
    url: t.Annotated[str, typer.Argument(metavar='URL_PATH', help='HTTP path')] = '/',
    quote_url: t.Annotated[
        bool, typer.Option('-Q', '--quote-url', help='Encode path with urllib.parse.quote but keep `,` and `*`')
    ] = False,
):
    logger.info(f'{method = }')

    client = es.Client(host=host)

    if not url.startswith('/'):
        url = '/' + url
    if quote_url:
        url = quote(string=url, safe=',*')
    logger.info(f'{url = }')

    headers = merge_dicts(http_header)
    logger.info(f'headers: {pformat(headers)}')

    params = merge_dicts(query_param)
    logger.info(f'params: {pformat(params)}')

    body = input_file and input_file.read()
    logger.debug(f'{body = }')

    response = client.transport.perform_request(method=method, url=url, headers=headers, params=params, body=body)
    logger.debug(f'{response = }')

    s = json_obj_to_line(response)
    logger.debug(f'{s = }')

    output_file.write(s)
