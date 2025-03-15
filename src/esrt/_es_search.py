from pprint import pformat
import sys
import typing as t

import typer

from . import _cli_params
from . import es
from .logging_ import logger
from .utils import json_obj_to_line
from .utils import merge_dicts


def es_search(
    host: t.Annotated[str, _cli_params.host],
    input_file: t.Annotated[t.Optional[typer.FileText], _cli_params.input_file] = None,
    output_file: t.Annotated[typer.FileTextWrite, _cli_params.output_file] = t.cast('typer.FileTextWrite', sys.stdout),
    index: t.Annotated[t.Optional[str], _cli_params.index] = None,
    doc_type: t.Annotated[t.Optional[str], _cli_params.doc_type] = None,
    query_param: t.Annotated[t.Optional[list[dict]], _cli_params.query_param] = None,
):
    client = es.Client(host=host)

    body = (input_file and input_file.read().strip()) or '{}'
    logger.debug(f'body: {pformat(body)}')

    params = merge_dicts(query_param)
    logger.info(f'params: {pformat(params)}')

    hits = client.search(
        index=index,
        doc_type=doc_type,
        body=body,
        params=params,
    )

    s = json_obj_to_line(hits)
    logger.debug(f'{s = }')

    output_file.write(s)
