from contextlib import nullcontext
from contextlib import redirect_stdout
from pprint import pformat
import sys
import time
import typing as t

from elasticsearch.helpers import streaming_bulk
import typer
from uvicorn.importer import import_from_string

from . import _cli_params
from . import es
from .logging_ import logger
from .utils import json_obj_to_line
from .utils import merge_dicts


def es_bulk(
    host: t.Annotated[str, _cli_params.host],
    input_file: t.Annotated[typer.FileText, _cli_params.input_file] = t.cast('typer.FileText', sys.stdin),
    output_file: t.Annotated[typer.FileTextWrite, _cli_params.output_file] = t.cast('typer.FileTextWrite', sys.stdout),
    progress: t.Annotated[bool, typer.Option(' /-S', ' /--no-progress')] = True,
    verbose: t.Annotated[bool, typer.Option('-v', '--verbose')] = False,
    index: t.Annotated[t.Optional[str], _cli_params.index] = None,
    params: t.Annotated[t.Optional[list[dict]], _cli_params.query_param] = None,
    handler: t.Annotated[
        t.Callable[[t.Iterable[str]], t.Iterable[str]],
        typer.Option(
            '-w',
            '--handler',
            parser=import_from_string,
            help='A callable handle actions. e.g. --handler esrt:DocHandler',
        ),
    ] = t.cast('t.Callable[[t.Iterable[str]], t.Iterable[str]]', 'esrt:DocHandler'),
    doc_type: t.Annotated[t.Optional[str], _cli_params.doc_type] = None,
    chunk_size: t.Annotated[int, typer.Option('-c', '--chunk-size')] = 500,
    max_chunk_bytes: t.Annotated[int, typer.Option('--max-chunk-bytes')] = 100 * 1024 * 1024,
    raise_on_error: t.Annotated[bool, typer.Option(' /--no-raise-on-error')] = True,
    raise_on_exception: t.Annotated[bool, typer.Option(' /--no-raise-on-exception')] = True,
    max_retries: t.Annotated[int, typer.Option('--max-retries')] = 3,
    initial_backoff: t.Annotated[int, typer.Option('--initial-backoff')] = 2,
    max_backoff: t.Annotated[int, typer.Option('--max-backoff')] = 600,
    kwargs: t.Annotated[t.Optional[list[dict]], _cli_params.kwargs] = None,
):
    logger.debug(pformat(locals()))
    client = es.Client(host=host)
    with redirect_stdout(sys.stderr):
        print('waiting for seconds to start', end=' ', flush=True)
        for i in range(5, -1, -1):
            print(i, end=' ', flush=True)
            time.sleep(1)
    _iterable = streaming_bulk(
        client=client,
        actions=handler(input_file),
        chunk_size=chunk_size,
        max_chunk_bytes=max_chunk_bytes,
        raise_on_error=raise_on_error,
        # expand_action_callback
        raise_on_exception=raise_on_exception,
        max_retries=max_retries,
        initial_backoff=initial_backoff,
        max_backoff=max_backoff,
        yield_ok=True,  # *
        index=index,
        doc_type=doc_type,
        params=merge_dicts(params),
        **merge_dicts(kwargs),
    )
    context = nullcontext(_iterable)
    if progress:
        context = typer.progressbar(iterable=_iterable, label='streaming_bulk', show_pos=True, file=sys.stderr)
    with context as items:
        success, failed = 0, 0
        for ok, item in items:
            if not ok:
                failed += 1
                with redirect_stdout(sys.stderr):
                    logger.warning(f'Failed to index {item}')
                with redirect_stdout(sys.stderr):
                    output_file.write(json_obj_to_line(item))
            else:
                success += 1
                if verbose:
                    with redirect_stdout(sys.stderr):
                        output_file.write(json_obj_to_line(item))
    with redirect_stdout(sys.stderr):
        print()  # TODO
        logger.warning(f'{success = }')
        logger.warning(f'{failed = }')
