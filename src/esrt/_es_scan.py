from contextlib import nullcontext
import json
from pprint import pformat
import sys
import typing as t

from elasticsearch.helpers import scan
import typer

from . import _cli_params
from . import es
from .logging_ import logger
from .utils import json_obj_to_line
from .utils import merge_dicts


def es_scan(
    host: t.Annotated[str, _cli_params.host],
    input_file: t.Annotated[t.Optional[typer.FileText], _cli_params.input_file] = None,
    output_file: t.Annotated[typer.FileTextWrite, _cli_params.output_file] = t.cast('typer.FileTextWrite', sys.stdout),
    progress: t.Annotated[bool, typer.Option()] = False,
    index: t.Annotated[t.Optional[str], _cli_params.index] = None,
    doc_type: t.Annotated[t.Optional[str], _cli_params.doc_type] = None,
    query_param: t.Annotated[t.Optional[list[dict]], _cli_params.query_param] = None,
    scroll: t.Annotated[str, typer.Option('--scroll', metavar='TIME', help='Scroll duration')] = '5m',
    raise_on_error: t.Annotated[bool, typer.Option(' /--no-raise-on-error')] = True,
    preserve_order: t.Annotated[bool, typer.Option('--preserve-order')] = False,
    size: t.Annotated[int, typer.Option('--size')] = 1000,
    request_timeout: t.Annotated[t.Optional[int], typer.Option('--request-timeout')] = None,
    clear_scroll: t.Annotated[bool, typer.Option(' /--keep-scroll')] = True,
    # scroll_kwargs
    kwargs: t.Annotated[t.Optional[list[dict]], _cli_params.kwargs] = None,
):
    client = es.Client(host=host)

    _body = (input_file and input_file.read().strip()) or '{}'
    body = _body and json.loads(_body)
    logger.debug(f'body: {pformat(body)}')

    # count
    once_params = merge_dicts(query_param)
    once_params['size'] = '1'
    once_search = client.search(
        index=index,
        doc_type=doc_type,
        body=body,
        params=once_params,  # *
    )
    total = once_search['hits']['total']
    logger.warning(f'{total = }')

    params = merge_dicts(query_param)
    logger.info(f'params: {pformat(params)}')

    scroll_kwargs = merge_dicts(kwargs)
    logger.info(f'scroll_kwargs: {pformat(scroll_kwargs)}')

    iterable = scan(
        client=client,
        index=index,
        doc_type=doc_type,
        query=body,
        params=params,
        scroll=scroll,
        raise_on_error=raise_on_error,
        preserve_order=preserve_order,
        size=size,
        request_timeout=request_timeout,
        clear_scroll=clear_scroll,
        **scroll_kwargs,
    )
    context = nullcontext(iterable)
    if progress:
        context = typer.progressbar(iterable=iterable, label='scan', show_pos=True, file=sys.stderr)
    with context as hits:
        for hit in hits:
            logger.info(f'{hit = }')
            output_file.write(json_obj_to_line(hit))
