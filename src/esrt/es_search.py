import sys
import typing as t

import typer

from . import cli_params
from . import es
from .utils import json_obj_to_line
from .utils import merge_dicts


def es_search(
    host: t.Annotated[str, cli_params.host],
    finput_body: t.Annotated[t.Optional[typer.FileText], cli_params.input_file] = None,
    foutput: t.Annotated[typer.FileTextWrite, cli_params.output_file] = t.cast(typer.FileTextWrite, sys.stdout),
    #
    index: t.Annotated[t.Optional[str], cli_params.index] = None,
    doc_type: t.Annotated[t.Optional[str], cli_params.doc_type] = None,
    params: t.Annotated[t.Optional[list[dict]], cli_params.query_param] = None,
):
    client = es.Client(host=host)
    hits = client.search(
        index=index,
        doc_type=doc_type,
        body=finput_body and finput_body.read().strip() or '{}',
        params=merge_dicts(params),
    )
    foutput.write(json_obj_to_line(hits))
