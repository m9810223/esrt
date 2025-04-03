[private]
default:
    just --fmt --unstable 2> /dev/null
    just --list --unsorted

ES_NAME := "esrt-es"
ES_PORT := "9200"

[group('Elasticsearch')]
start-es_server:
    docker run --name {{ ES_NAME }} --rm -itd --platform=linux/amd64 -p {{ ES_PORT }}:9200 elasticsearch:5.6.9-alpine

[group('Elasticsearch')]
remove-es_server:
    docker rm {{ ES_NAME }} -f

[group('Elasticsearch')]
restart-es_server: remove-es_server start-es_server

ESRT := "uv run esrt"
ES_HOST := "localhost:" + ES_PORT
JQ_ES_HITS := "jq '.hits.hits[]'"

[group('esrt')]
test-es-ping:
    #!/usr/bin/env bash -eux
    {{ ESRT }} es ping {{ ES_HOST }}

[group('esrt')]
test-es-request:
    #!/usr/bin/env bash -eux

    {{ ESRT }} es request {{ ES_HOST }} -X HEAD
    {{ ESRT }} es request {{ ES_HOST }} -X PUT --url /my-index 2>/dev/null || true

    {{ ESRT }} es request {{ ES_HOST }} --url /_cat/indices
    {{ ESRT }} es request {{ ES_HOST }} --url /_cat/indices?v
    {{ ESRT }} es request {{ ES_HOST }} --url '/_cat/indices?v&format=json'
    {{ ESRT }} es request {{ ES_HOST }} --url /_cat/indices -p v= -p format=json

[group('esrt')]
test-es-bulk:
    #!/usr/bin/env bash -eux

    {{ ESRT }} es bulk {{ ES_HOST }} -y -f examples/bulk.ndjson

    echo '
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index", "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    ' | {{ ESRT }} es bulk {{ ES_HOST }} -y -f -

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

[group('esrt')]
test-es-search:
    #!/usr/bin/env bash -eux

    {{ ESRT }} es search {{ ES_HOST }} | {{ JQ_ES_HITS }} -c

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

[group('esrt')]
test-es-scan:
    #!/usr/bin/env bash -eux

    {{ ESRT }} es scan {{ ES_HOST }} -y

    {{ ESRT }} es scan {{ ES_HOST }} -y -f - <<EOF
    {"query": {"term": {"field1": "cc"}}}
    EOF

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

[group('esrt')]
test-es-others:
    python examples/create-massive-docs.py | tee _.ndjson | {{ ESRT }} es bulk {{ ES_HOST }} -y -f -
    python examples/copy-more-docs.py | {{ ESRT }} es bulk {{ ES_HOST }} -y -f - -w examples.copy-more-docs:handle

[group('esrt')]
test-es: restart-es_server test-es-ping test-es-request test-es-bulk test-es-search test-es-scan test-es-others
