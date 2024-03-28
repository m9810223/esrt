# esrt - Elasticsearch Request Tool

[![pypi](https://img.shields.io/pypi/v/esrt.svg)](https://pypi.python.org/pypi/esrt)

```sh
pipx install esrt
```

## Example

You can start an es service with docker.

```sh
docker run --rm -it --platform=linux/amd64 -p 9200:9200 elasticsearch:5.6.9-alpine
```

---

## `r` - Send a request

```sh
# create a index: `my-index`
esrt r localhost -X PUT /my-index
# ->
# {"acknowledged": true, "shards_acknowledged": true, "index": "my-index"}
```

```sh
esrt r localhost -X GET _cat/indices -p 'v&format=json' -p 's=index'
# ->
# [{"health": "yellow", "status": "open", "index": "my-index", "uuid": "FQjeEOKQT8aroL2dgO7yDg", "pri": "5", "rep": "1", "docs.count": "0", "docs.deleted": "0", "store.size": "324b", "pri.store.size": "324b"}]
```

*Note: esrt won't keep `-p pretty` format by default, but you can use `jq` instead.*

```sh
esrt r localhost -X GET _cat/indices -p 'v&format=json' -p 's=index' | jq
# ->
# [
#   {
#     "health": "yellow",
#     "status": "open",
#     "index": "my-index",
#     "uuid": "FQjeEOKQT8aroL2dgO7yDg",
#     "pri": "5",
#     "rep": "1",
#     "docs.count": "0",
#     "docs.deleted": "0",
#     "store.size": "810b",
#     "pri.store.size": "810b"
#   }
# ]
```

---

## `t` - Transmit data (`streaming_bulk`)

bulk with data from file:

```json
// dev.ndjson
{ "_op_type": "index",  "_index": "my-index", "_type": "type1", "_id": "1", "field1": "ii" }
{ "_op_type": "delete", "_index": "my-index", "_type": "type1", "_id": "1" }
{ "_op_type": "create", "_index": "my-index", "_type": "type1", "_id": "1", "field1": "cc" }
{ "_op_type": "update", "_index": "my-index", "_type": "type1", "_id": "1", "doc": {"field2": "uu"} }
```

```sh
esrt t localhost -d dev.ndjson
# ->
# <Client([{'host': 'localhost', 'port': 9200}])>
# streaming_bulk  [####################################]  4
#
# success = 0
# failed = 0
```

---

```sh
# Piping `heredoc` also works. And `-d` can be omitted.
cat <<EOF | esrt t localhost
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
EOF
# ->
# <Client([{'host': 'localhost', 'port': 9200}])>
# streaming_bulk  [####################################]  3
#
# success = 0
# failed = 0
```

---

Pipe `_search` result and update `_index` with `customized handler` to do more operations before bulk!

```sh
alias jq_es_hits="jq '.hits.hits.[]' -c"
#
esrt r localhost -X GET /my-index/_search | jq_es_hits | esrt t localhost -w dev:MyHandler # <- `dev.py`
# ->
# <Client([{'host': 'localhost', 'port': 9200}])>
# streaming_bulk  [####################################]  1
#
# success = 0
# failed = 0
```

```py
# dev.py
import json
import typing as t

from esrt import DocHandler


class MyHandler(DocHandler):
    def handle_one(self, action: str):
        obj = json.loads(action)
        prefix = 'new-'
        if not t.cast(str, obj['_index']).startswith(prefix):
            obj['_index'] = prefix + obj['_index']
        return obj


# function style
def my_handler(actions: t.Iterable[str]):
    for action in actions:
        yield json.loads(action)
```

---

## `e` Search docs

```sh
esrt e localhost | jq_es_hits
# ->
# {"_index":"my-index-2","_type":"type1","_id":"2","_score":1.0,"_source":{"field1":"22"}}
# {"_index":"my-index","_type":"type1","_id":"1","_score":1.0,"_source":{"field1":"cc","field2":"uu"}}
# {"_index":"my-index-2","_type":"type1","_id":"1","_score":1.0,"_source":{"field1":"11"}}
# {"_index":"new-my-index","_type":"type1","_id":"1","_score":1.0,"_source":{"field1":"cc","field2":"uu"}}
# {"_index":"my-index-2","_type":"type1","_id":"3","_score":1.0,"_source":{"field1":"33"}}
```

```sh
cat <<EOF | esrt e localhost -d - | jq_es_hits
{"query": {"term": {"_index": "new-my-index"}}}
EOF
# ->
# {"_index":"new-my-index","_type":"type1","_id":"1","_score":1.0,"_source":{"field1":"cc","field2":"uu"}}
```

## `s` - Search and `Scroll`

```sh
esrt s localhost
# ->
# total = 5
# {"_index": "my-index-2", "_type": "type1", "_id": "2", "_score": null, "_source": {"field1": "22"}, "sort": [0]}
# {"_index": "my-index", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "cc", "field2": "uu"}, "sort": [0]}
# {"_index": "my-index-2", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "11"}, "sort": [0]}
# {"_index": "new-my-index", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "cc", "field2": "uu"}, "sort": [0]}
# {"_index": "my-index-2", "_type": "type1", "_id": "3", "_score": null, "_source": {"field1": "33"}, "sort": [0]}
```

```sh
cat <<EOF | esrt s localhost -d -
{"query": {"term": {"field1": "cc"}}}
EOF
# ->
# total = 2
# {"_index": "my-index", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "cc", "field2": "uu"}, "sort": [0]}
# {"_index": "new-my-index", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "cc", "field2": "uu"}, "sort": [0]}
```
