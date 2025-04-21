[private]
default:
    just --fmt --unstable 2> /dev/null
    just --list --unsorted

ES_NAME := "esrt-es"
ES_PORT := "9200"

[group('Elasticsearch')]
start-es_server:
    docker run --name {{ ES_NAME }} --rm -itd --platform=linux/amd64 -p {{ ES_PORT }}:9200 elasticsearch:5.6.9-alpine

[private]
es_server-install-sql_plugin:
    docker exec {{ ES_NAME }} elasticsearch-plugin list | grep sql || docker exec {{ ES_NAME }} elasticsearch-plugin install https://github.com/NLPchina/elasticsearch-sql/releases/download/5.6.9.0/elasticsearch-sql-5.6.9.0.zip || true
    docker restart {{ ES_NAME }}

[group('Elasticsearch')]
remove-es_server:
    docker rm {{ ES_NAME }} -f

[group('Elasticsearch')]
restart-es_server: remove-es_server start-es_server

ESRT := "uv run esrt"
ES_HOST := "localhost:" + ES_PORT
JQ_ES_HITS := "jq '.hits.hits[]'"

[group('esrt')]
test-es: && restart-es_server test-es-ping test-es-request test-es-bulk test-es-search test-es-scan test-es-others
    rm -f {{ RECORD_LOG_FILE }}

TEST_LOG_FILE := "_.test.log"
RECORD_LOG_FILE := "record.txt"
[private]
RECORD_CMD := "echo '\n---' >>" + RECORD_LOG_FILE + "; PS4=$'\n>>> '; exec > >(tee -a " + RECORD_LOG_FILE + ") 2>&1; set -eux"

[group('esrt')]
test-es-request:
    #!/usr/bin/env bash
    {{ RECORD_CMD }}

    {{ ESRT }} es request {{ ES_HOST }}
    {{ ESRT }} es request {{ ES_HOST }} -X HEAD
    {{ ESRT }} es request {{ ES_HOST }} -v
    {{ ESRT }} es request {{ ES_HOST }} -o {{ TEST_LOG_FILE }}
    {{ ESRT }} es request {{ ES_HOST }} -H a=1 -H b=false
    {{ ESRT }} es request {{ ES_HOST }} -u /_cat/indices -v -p v=true -p s=index
    {{ ESRT }} es request {{ ES_HOST }} -X PUT --url /my-index 2>/dev/null || true

    {{ ESRT }} es request {{ ES_HOST }} --url /_cat/indices
    {{ ESRT }} es request {{ ES_HOST }} --url /_cat/indices?v
    {{ ESRT }} es request {{ ES_HOST }} --url '/_cat/indices?v&format=json'
    {{ ESRT }} es request {{ ES_HOST }} --url /_cat/indices -p v= -p format=json

[group('esrt')]
test-es-sql: es_server-install-sql_plugin
    #!/usr/bin/env bash
    {{ RECORD_CMD }}

    echo '
    select * from my-index
    ' | {{ ESRT }} es sql {{ ES_HOST }}

    echo '
    select * from my-index
    ' | {{ ESRT }} es sql {{ ES_HOST }} -f -

    {{ ESRT }} es sql {{ ES_HOST }} -f - <<<'
    select * from my-index
    '

    {{ ESRT }} es sql {{ ES_HOST }} -f - <<EOF
    select * from my-index
    EOF

    {{ ESRT }} es sql {{ ES_HOST }} -d'
    select * from my-index
    '

    {{ ESRT }} es sql {{ ES_HOST }} -d 'select * from my-index' -v
    {{ ESRT }} es sql {{ ES_HOST }} -d 'select * from my-index' -o {{ TEST_LOG_FILE }}
    {{ ESRT }} es sql {{ ES_HOST }} -d 'select * from my-index' --no-pretty

[group('esrt')]
test-es-ping:
    #!/usr/bin/env bash
    {{ RECORD_CMD }}

    {{ ESRT }} es ping {{ ES_HOST }}
    {{ ESRT }} es ping {{ ES_HOST }} -v
    {{ ESRT }} es ping {{ ES_HOST }} -I

[group('esrt')]
test-es-bulk:
    #!/usr/bin/env bash
    {{ RECORD_CMD }}

    echo '
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    ' | {{ ESRT }} es bulk {{ ES_HOST }} -y

    echo '
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    ' | {{ ESRT }} es bulk {{ ES_HOST }} -y -f -

    {{ ESRT }} es bulk {{ ES_HOST }} -y -f - <<<'
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    '

    {{ ESRT }} es bulk {{ ES_HOST }} -y -f - <<EOF
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    EOF

    {{ ESRT }} es bulk {{ ES_HOST }} -y -d'
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    '

    {{ ESRT }} es request {{ ES_HOST }} --url /my-index-2/_search | {{ JQ_ES_HITS }} -c | {{ ESRT }} es bulk {{ ES_HOST }} -y -f - -w examples.my-handlers:handle

    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson -v
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson -n
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson -o {{ TEST_LOG_FILE }}
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson --no-pretty
    {{ ESRT }} es bulk {{ ES_HOST }} -y -i my-index-i -d '{ "_type": "type1", "_id": "1", "field1": "ii" }'
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson --chunk_size 1
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson --max_chunk_bytes 1
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson --raise_on_error
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson --raise_on_exception
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson --max_retries 0
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson --initial_backoff 0
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson --max_backoff 0
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson --yield_ok
    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson --request_timeout 0

[group('esrt')]
test-es-search:
    #!/usr/bin/env bash
    {{ RECORD_CMD }}

    echo '
    {"query": {"term": {"_index": "new-my-index-2"}}}
    ' | {{ ESRT }} es search {{ ES_HOST }} | {{ JQ_ES_HITS }} -c

    echo '
    {"query": {"term": {"_index": "new-my-index-2"}}}
    ' | {{ ESRT }} es search {{ ES_HOST }} -f - | {{ JQ_ES_HITS }} -c

    {{ ESRT }} es search {{ ES_HOST }} -f - <<<'
    {"query": {"term": {"_index": "new-my-index-2"}}}
    ' | {{ JQ_ES_HITS }} -c

    {{ ESRT }} es search {{ ES_HOST }} -f - <<EOF | {{ JQ_ES_HITS }} -c
    {"query": {"term": {"_index": "new-my-index-2"}}}
    EOF

    {{ ESRT }} es search {{ ES_HOST }} -d '
    {"query": {"term": {"_index": "new-my-index-2"}}}
    ' | {{ JQ_ES_HITS }} -c

    {{ ESRT }} es search {{ ES_HOST }} | {{ JQ_ES_HITS }} -c
    {{ ESRT }} es search {{ ES_HOST }} -v
    {{ ESRT }} es search {{ ES_HOST }} -o {{ TEST_LOG_FILE }}
    {{ ESRT }} es search {{ ES_HOST }} --no-pretty
    {{ ESRT }} es search {{ ES_HOST }} -i my-index
    {{ ESRT }} es search {{ ES_HOST }} -p from=1
    {{ ESRT }} es search {{ ES_HOST }} --doc_type type1

[group('esrt')]
test-es-scan:
    #!/usr/bin/env bash
    {{ RECORD_CMD }}

    echo '
    {"query": {"term": {"field1": "cc"}}}
    ' | {{ ESRT }} es scan {{ ES_HOST }} -y

    echo '
    {"query": {"term": {"field1": "cc"}}}
    ' | {{ ESRT }} es scan {{ ES_HOST }} -y -f -

    {{ ESRT }} es scan {{ ES_HOST }} -y -f - <<<'
    {"query": {"term": {"field1": "cc"}}}
    '

    {{ ESRT }} es scan {{ ES_HOST }} -y -f - <<EOF
    {"query": {"term": {"field1": "cc"}}}
    EOF

    {{ ESRT }} es scan {{ ES_HOST }} -y -d'
    {"query": {"term": {"field1": "cc"}}}
    '

    {{ ESRT }} es scan {{ ES_HOST }} -y
    {{ ESRT }} es scan {{ ES_HOST }} -y -v
    {{ ESRT }} es scan {{ ES_HOST }} -n
    {{ ESRT }} es scan {{ ES_HOST }} -y -o {{ TEST_LOG_FILE }}
    {{ ESRT }} es scan {{ ES_HOST }} -y --no-pretty
    {{ ESRT }} es scan {{ ES_HOST }} -y -i my-index
    {{ ESRT }} es scan {{ ES_HOST }} -y -p _source=false
    {{ ESRT }} es scan {{ ES_HOST }} -y --doc_type type1
    {{ ESRT }} es scan {{ ES_HOST }} -y --scroll 1s
    {{ ESRT }} es scan {{ ES_HOST }} -y --raise_on_error
    {{ ESRT }} es scan {{ ES_HOST }} -y -N 1
    {{ ESRT }} es scan {{ ES_HOST }} -y -t 1
    # {{ ESRT }} es scan {{ ES_HOST }} -y --scroll_kwargs rest_total_hits_as_int=

[group('esrt')]
test-es-others:
    python examples/create-massive-docs.py | tee _.ndjson | {{ ESRT }} es bulk {{ ES_HOST }} -y -f -
    python examples/copy-more-docs.py | {{ ESRT }} es bulk {{ ES_HOST }} -y -f - -w examples.copy-more-docs:handle
