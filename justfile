[private]
default:
    just --fmt --unstable 2> /dev/null
    just --list --unsorted

ES_NAME := "esrt-es"
ES_PORT := "9200"

[group('Elasticsearch')]
start-test_es:
    docker run --name {{ ES_NAME }} --rm -itd --platform=linux/amd64 -p {{ ES_PORT }}:9200 elasticsearch:5.6.9-alpine

[group('Elasticsearch')]
remove-test_es:
    docker rm {{ ES_NAME }} -f

[group('Elasticsearch')]
restart-test_es: remove-test_es start-test_es

ESRT := "uv run esrt"
ES_HOST := "localhost:" + ES_PORT
JQ_ES_HITS := "jq '.hits.hits[]'"

[group('esrt')]
test-ping:
    #!/usr/bin/env bash -eux
    {{ ESRT }} ping {{ ES_HOST }}

[group('esrt')]
test-request:
    #!/usr/bin/env bash -eux

    {{ ESRT }} request {{ ES_HOST }} -X HEAD
    {{ ESRT }} request {{ ES_HOST }} -X PUT -u /my-index 2>/dev/null || true

    {{ ESRT }} request {{ ES_HOST }} -u _cat/indices
    {{ ESRT }} request {{ ES_HOST }} -u _cat/indices?v
    {{ ESRT }} request {{ ES_HOST }} -u "_cat/indices?v&format=json"
    {{ ESRT }} request {{ ES_HOST }} -u _cat/indices -p v= -p format=json

[group('esrt')]
test-bulk:
    #!/usr/bin/env bash -eux

    {{ ESRT }} bulk {{ ES_HOST }} -y -f examples/bulk.ndjson

    echo '
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    ' | {{ ESRT }} bulk {{ ES_HOST }} -y -f -

    echo '
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    ' | {{ ESRT }} bulk {{ ES_HOST }} -y -f -

    {{ ESRT }} bulk {{ ES_HOST }} -y -f - <<<'
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    '

    {{ ESRT }} bulk {{ ES_HOST }} -y -f - <<EOF
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    EOF

    {{ ESRT }} bulk {{ ES_HOST }} -y -d'
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
    { "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
    '

    {{ ESRT }} request {{ ES_HOST }} -u my-index-2/_search | {{ JQ_ES_HITS }} -c | {{ ESRT }} bulk {{ ES_HOST }} -y -f - -w examples.my-handlers:handle

[group('esrt')]
test-search:
    #!/usr/bin/env bash -eux

    {{ ESRT }} search {{ ES_HOST }} | {{ JQ_ES_HITS }} -c

    echo '
    {"query": {"term": {"_index": "new-my-index-2"}}}
    ' | {{ ESRT }} search {{ ES_HOST }} | {{ JQ_ES_HITS }} -c

    echo '
    {"query": {"term": {"_index": "new-my-index-2"}}}
    ' | {{ ESRT }} search {{ ES_HOST }} -f - | {{ JQ_ES_HITS }} -c

    {{ ESRT }} search {{ ES_HOST }} -f - <<<'
    {"query": {"term": {"_index": "new-my-index-2"}}}
    ' | {{ JQ_ES_HITS }} -c

    {{ ESRT }} search {{ ES_HOST }} -f - <<EOF | {{ JQ_ES_HITS }} -c
    {"query": {"term": {"_index": "new-my-index-2"}}}
    EOF

    {{ ESRT }} search {{ ES_HOST }} -d '
    {"query": {"term": {"_index": "new-my-index-2"}}}
    ' | {{ JQ_ES_HITS }} -c

[group('esrt')]
test-scan:
    #!/usr/bin/env bash -eux

    {{ ESRT }} scan {{ ES_HOST }} -y

    {{ ESRT }} scan {{ ES_HOST }} -y -f - <<EOF
    {"query": {"term": {"field1": "cc"}}}
    EOF

    echo '
    {"query": {"term": {"field1": "cc"}}}
    ' | {{ ESRT }} scan {{ ES_HOST }} -y

    echo '
    {"query": {"term": {"field1": "cc"}}}
    ' | {{ ESRT }} scan {{ ES_HOST }} -y -f -

    {{ ESRT }} scan {{ ES_HOST }} -y -f - <<<'
    {"query": {"term": {"field1": "cc"}}}
    '

    {{ ESRT }} scan {{ ES_HOST }} -y -f - <<EOF
    {"query": {"term": {"field1": "cc"}}}
    EOF

    {{ ESRT }} scan {{ ES_HOST }} -y -d'
    {"query": {"term": {"field1": "cc"}}}
    '

[group('esrt')]
test-others:
    python examples/create-massive-docs.py | tee -a _.ndjson | {{ ESRT }} bulk {{ ES_HOST }} -y -f -
    python examples/copy-more-docs.py | {{ ESRT }} bulk {{ ES_HOST }} -y -f - -w examples.copy-more-docs:handle

[group('esrt')]
test: restart-test_es test-ping test-request test-bulk test-search test-scan test-others
