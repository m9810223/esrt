from contextlib import nullcontext
from contextlib import redirect_stdout
import json
import sys
import typing as t

from elasticsearch.helpers import scan
import typer

from . import cli_params
from . import es
from .utils import json_obj_to_line
from .utils import merge_dicts


def es_scan(
    host: t.Annotated[str, cli_params.host],
    input_file: t.Annotated[t.Optional[typer.FileText], cli_params.input_file] = None,
    output_file: t.Annotated[typer.FileTextWrite, cli_params.output_file] = t.cast(typer.FileTextWrite, sys.stdout),
    #
    progress: t.Annotated[bool, typer.Option()] = False,
    verbose: t.Annotated[bool, typer.Option('-v', '--verbose')] = False,
    #
    index: t.Annotated[t.Optional[str], cli_params.index] = None,
    doc_type: t.Annotated[t.Optional[str], cli_params.doc_type] = None,
    params: t.Annotated[t.Optional[list[dict]], cli_params.query_param] = None,
    #
    scroll: t.Annotated[str, typer.Option('--scroll', metavar='TIME', help='Scroll duration')] = '5m',
    raise_on_error: t.Annotated[bool, typer.Option(' /--no-raise-on-error')] = True,
    preserve_order: t.Annotated[bool, typer.Option('--preserve-order')] = False,
    size: t.Annotated[int, typer.Option('--size')] = 1000,
    request_timeout: t.Annotated[t.Optional[int], typer.Option('--request-timeout')] = None,
    clear_scroll: t.Annotated[bool, typer.Option(' /--keep-scroll')] = True,
    # scroll_kwargs
    kwargs: t.Annotated[t.Optional[list[dict]], cli_params.kwargs] = None,
):
    client = es.Client(host=host)
    body = input_file and input_file.read().strip() or '{}'
    _once_params = merge_dicts(params)
    _once_params['size'] = '1'
    _once = client.search(
        index=index,
        doc_type=doc_type,
        body=body and json.loads(body),
        params=_once_params,  # *
    )
    total = _once['hits']['total']
    with redirect_stdout(sys.stderr):
        print(f'{total = }')
    _iterable = scan(
        client=client,
        index=index,
        doc_type=doc_type,
        query=body and json.loads(body),
        params=merge_dicts(params),
        #
        scroll=scroll,
        raise_on_error=raise_on_error,
        preserve_order=preserve_order,
        size=size,
        request_timeout=request_timeout,
        clear_scroll=clear_scroll,
        # scroll_kwargs
        **merge_dicts(kwargs),
    )
    context = nullcontext(_iterable)
    if progress:
        context = typer.progressbar(iterable=_iterable, label='scan', show_pos=True, file=sys.stderr)
    with context as hits:
        for hit in hits:
            if verbose:
                with redirect_stdout(sys.stderr):
                    print(hit)
            output_file.write(json_obj_to_line(hit))
