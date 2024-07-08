from contextlib import nullcontext
from contextlib import redirect_stdout
import json
import sys
import time
import typing as t
from urllib.parse import quote

from elasticsearch.helpers import scan
from elasticsearch.helpers import streaming_bulk
import typer
from typer.core import TyperGroup
from uvicorn.importer import import_from_string

from . import es
from .__version__ import VERSION
from .cli_help import Help
from .cli_mixins import AliasGroupMixin
from .cli_mixins import OrderGroupMixin
from .utils import json_obj_to_line
from .utils import merge_dicts
from .utils import parse_header
from .utils import parse_params


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
            typer.style('CLI use Python Elasticsearch==6.8.2', fg=typer.colors.BLACK, bold=True),
        ]
    ),
    #
    pretty_exceptions_enable=False,
)

_host_annotated = t.Annotated[
    str,
    typer.Argument(
        metavar='ES_HOST', help='Elasticsearch host. e.g. 127.0.0.1 -> http://127.0.0.1:9200'
    ),
]
_index_annotation = typer.Option(
    '-i', '--index', metavar='INDEX', help='A comma-separated list of index names to search'
)
_method_annotated = t.Annotated[
    str,
    typer.Option(
        '-X', '--method', '--request', metavar='HTTP_METHOD', parser=str.upper, help='HTTP method'
    ),
]
_path_annotated = t.Annotated[str, typer.Argument(metavar='URL_PATH', help='HTTP path')]
_params_annotated = t.Annotated[
    t.Optional[list[dict]],
    typer.Option('-p', '--params', metavar='QUERY_PARAM', parser=parse_params, help='HTTP params'),
]
_headers_annotated = t.Annotated[
    t.Optional[list[dict]],
    typer.Option('-H', '--header', metavar='HTTP_HEADER', parser=parse_header, help='HTTP headers'),
]
_kwargs_annotated = t.Annotated[
    t.Optional[list[dict]], typer.Option('-k', '--kwargs', parser=parse_params)
]
#
_finput_annotation = typer.Option('-d', '--data', metavar='FILE', help='Input file')
_foutput_annotated = t.Annotated[
    typer.FileTextWrite, typer.Option('-o', '--output', metavar='FILE', help='Output file')
]
#
_doc_type_annotated = t.Annotated[
    t.Optional[str], typer.Option('-t', '--type', metavar='DOC_TYPE', help='Document type')
]
#
_chunk_size_annotated = t.Annotated[int, typer.Option('-c', '--chunk-size')]


@app.command('e / search', no_args_is_help=True, short_help=Help.e_search)
def search(
    host: _host_annotated,
    finput_body: t.Annotated[t.Optional[typer.FileText], _finput_annotation] = None,
    foutput: _foutput_annotated = t.cast(typer.FileTextWrite, sys.stdout),
    #
    index: t.Annotated[t.Optional[str], _index_annotation] = None,
    doc_type: _doc_type_annotated = None,
    params: _params_annotated = None,
):
    client = es.Client(host=host)
    hits = client.search(
        index=index,
        doc_type=doc_type,
        body=finput_body and finput_body.read().strip() or '{}',
        params=merge_dicts(params),
    )
    foutput.write(json_obj_to_line(hits))


@app.command(name='s / scan / scroll', no_args_is_help=True, short_help=Help.s_scan)
def scan_(
    host: _host_annotated,
    finput_body: t.Annotated[t.Optional[typer.FileText], _finput_annotation] = None,
    foutput: _foutput_annotated = t.cast(typer.FileTextWrite, sys.stdout),
    #
    progress: t.Annotated[bool, typer.Option()] = False,
    verbose: t.Annotated[bool, typer.Option('-v', '--verbose')] = False,
    #
    index: t.Annotated[t.Optional[str], _index_annotation] = None,
    doc_type: _doc_type_annotated = None,
    params: _params_annotated = None,
    #
    scroll: t.Annotated[
        str, typer.Option('--scroll', metavar='TIME', help='Scroll duration')
    ] = '5m',
    raise_on_error: t.Annotated[bool, typer.Option(' /--no-raise-on-error')] = True,
    preserve_order: t.Annotated[bool, typer.Option('--preserve-order')] = False,
    size: t.Annotated[int, typer.Option('--size')] = 1000,
    request_timeout: t.Annotated[t.Optional[int], typer.Option('--request-timeout')] = None,
    clear_scroll: t.Annotated[bool, typer.Option(' /--keep-scroll')] = True,
    # scroll_kwargs
    kwargs: _kwargs_annotated = None,
):
    client = es.Client(host=host)
    body = finput_body and finput_body.read().strip() or '{}'
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
        context = typer.progressbar(
            iterable=_iterable, label='scan', show_pos=True, file=sys.stderr
        )
    with context as hits:
        for hit in hits:
            if verbose:
                with redirect_stdout(sys.stderr):
                    print(hit)
            foutput.write(json_obj_to_line(hit))


@app.command(name='r / request / api', no_args_is_help=True, short_help=Help.r_request)
def perform_request(
    host: _host_annotated,
    finput_body: t.Annotated[t.Optional[typer.FileText], _finput_annotation] = None,
    foutput: _foutput_annotated = t.cast(typer.FileTextWrite, sys.stdout),
    #
    method: _method_annotated = 'GET',
    url: _path_annotated = '/',
    quote_url: t.Annotated[
        bool,
        typer.Option(
            '-Q', '--quote-url', help='Encode path with urllib.parse.quote but keep `,` and `*`'
        ),
    ] = False,
    params: _params_annotated = None,
    headers: _headers_annotated = None,
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


@app.command(name='t / transmit / bulk', no_args_is_help=True, short_help=Help.t_transmit)
def streaming_bulk_(
    host: _host_annotated,
    finput_body: t.Annotated[typer.FileText, _finput_annotation] = t.cast(
        typer.FileText, sys.stdin
    ),
    foutput: _foutput_annotated = t.cast(typer.FileTextWrite, sys.stdout),
    #
    progress: t.Annotated[bool, typer.Option(' /-S', ' /--no-progress')] = True,
    verbose: t.Annotated[bool, typer.Option('-v', '--verbose')] = False,
    #
    index: t.Annotated[t.Optional[str], _index_annotation] = None,
    params: _params_annotated = None,
    handler: t.Annotated[
        t.Callable[[t.Iterable[str]], t.Iterable[str]],
        typer.Option(
            '-w',
            '--handler',
            parser=import_from_string,
            help='A callable handle actions. e.g. --handler esrt:DocHandler',
        ),
    ] = t.cast(t.Callable[[t.Iterable[str]], t.Iterable[str]], 'esrt:DocHandler'),
    doc_type: _doc_type_annotated = None,
    #
    chunk_size: _chunk_size_annotated = 500,
    max_chunk_bytes: t.Annotated[int, typer.Option('--max-chunk-bytes')] = 100 * 1024 * 1024,
    raise_on_error: t.Annotated[bool, typer.Option(' /--no-raise-on-error')] = True,
    raise_on_exception: t.Annotated[bool, typer.Option(' /--no-raise-on-exception')] = True,
    max_retries: t.Annotated[int, typer.Option('--max-retries')] = 3,
    initial_backoff: t.Annotated[int, typer.Option('--initial-backoff')] = 2,
    max_backoff: t.Annotated[int, typer.Option('--max-backoff')] = 600,
    #
    kwargs: _kwargs_annotated = None,
):
    client = es.Client(host=host)
    with redirect_stdout(sys.stderr):
        print(client)
        print('waiting for seconds to start', end=' ', flush=True)
        for i in range(5, -1, -1):
            print(i, end=' ', flush=True)
            time.sleep(1)
    _iterable = streaming_bulk(
        client=client,
        actions=handler(finput_body),
        #
        chunk_size=chunk_size,
        max_chunk_bytes=max_chunk_bytes,
        raise_on_error=raise_on_error,
        # expand_action_callback
        raise_on_exception=raise_on_exception,
        max_retries=max_retries,
        initial_backoff=initial_backoff,
        max_backoff=max_backoff,
        yield_ok=True,  # *
        #
        index=index,
        doc_type=doc_type,
        params=merge_dicts(params),
        #
        **merge_dicts(kwargs),
    )
    context = nullcontext(_iterable)
    if progress:
        context = typer.progressbar(
            iterable=_iterable, label='streaming_bulk', show_pos=True, file=sys.stderr
        )
    with context as items:
        success, failed = 0, 0
        for ok, item in items:
            if not ok:
                failed += 1
                with redirect_stdout(sys.stderr):
                    print(f'Failed to index {item}')
                with redirect_stdout(sys.stderr):
                    foutput.write(json_obj_to_line(item))
            else:
                success += 1
                if verbose:
                    with redirect_stdout(sys.stderr):
                        foutput.write(json_obj_to_line(item))
    with redirect_stdout(sys.stderr):
        print()
        print(f'{success = }')
        print(f'{failed = }')


@app.command(name='sql', no_args_is_help=True, short_help=Help.sql)
def sql(
    host: _host_annotated,
    sql_stmt: typer.FileText,
    foutput: _foutput_annotated = t.cast(typer.FileTextWrite, sys.stdout),
):
    return perform_request(
        host=host,
        finput_body=sql_stmt,
        foutput=foutput,
        method='POST',  # *
        url='/_sql',  # *
    )
