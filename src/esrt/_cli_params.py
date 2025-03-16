import typer

from .utils import parse_header
from .utils import parse_params


host = typer.Argument(metavar='ES_HOST', help='Elasticsearch host. Use port 9200 if no scheme or port is provided.')
index = typer.Option('-i', '--index', metavar='INDEX', help='A comma-separated list of index names to search')
doc_type = typer.Option('-t', '--doc-type', metavar='DOC_TYPE', help='Document type')

query_param = typer.Option(
    '-p', '--http-query-params', metavar='QUERY_PARAM', parser=parse_params, help='HTTP query params'
)
http_header = typer.Option('-H', '--http-header', metavar='HTTP_HEADER', parser=parse_header, help='HTTP headers')

kwargs = typer.Option('-k', '--kwargs', parser=parse_params)

input_file = typer.Option('-f', '--input-file', metavar='FILE', help='Input file')
output_file = typer.Option('-o', '--output-file', metavar='FILE', help='Output file')
