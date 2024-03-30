# esrt - Elasticsearch Request Tool

[![pypi](https://img.shields.io/pypi/v/esrt.svg)](https://pypi.python.org/pypi/esrt)

```sh
pip install pipx
pipx install esrt -f
esrt --install-completion # Install completion for the current shell.
```

## Commands

- `e`: search
- `s`: scan / scroll
- `r`: request / api / a
- `t`: transmit / bulk / b
- `sql`: sql / query / q

---

## Example

You can start an es service with docker.

```sh
docker run --rm -itd --platform=linux/amd64 -p 9200:9200 elasticsearch:5.6.9-alpine
```

---

## `r` - Send a request

Check server:

```sh
esrt r localhost -X HEAD
# ->
# true
```

Create a index:

```sh
esrt r localhost -X PUT /my-index
# ->
# {"acknowledged": true, "shards_acknowledged": true, "index": "my-index"}
```

Cat it:

```sh
esrt r localhost -X GET _cat/indices -p 'v&format=json' -p 's=index'
# ->
# [{"health": "yellow", "status": "open", "index": "my-index", "uuid": "avrhX1hzQLyfEGvXsA96NA", "pri": "5", "rep": "1", "docs.count": "0", "docs.deleted": "0", "store.size": "324b", "pri.store.size": "324b"}]
```

*`esrt` doesn't keep `-p pretty` format, but you can use `jq`.*

```sh
esrt r localhost -X GET _cat/indices -p 'v&format=json' -p 's=index' | jq
# ->
# [
#   {
#     "health": "yellow",
#     "status": "open",
#     "index": "my-index",
#     "uuid": "avrhX1hzQLyfEGvXsA96NA",
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

Bulk with data from file `examples/bulk.ndjson`:

```json
{ "_op_type": "index",  "_index": "my-index", "_type": "type1", "_id": "1", "field1": "ii" }
{ "_op_type": "delete", "_index": "my-index", "_type": "type1", "_id": "1" }
{ "_op_type": "create", "_index": "my-index", "_type": "type1", "_id": "1", "field1": "cc" }
{ "_op_type": "update", "_index": "my-index", "_type": "type1", "_id": "1", "doc": {"field2": "uu"} }
```

```sh
esrt t localhost -d examples/bulk.ndjson
# ->
# <Client([{'host': 'localhost', 'port': 9200}])>
# streaming_bulk  [####################################]  4

# success = 4
# failed = 0
```

---

Piping `heredoc` also works. And `-d` can be omitted.

```sh
cat <<EOF | esrt t localhost
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
EOF
# ->
# <Client([{'host': 'localhost', 'port': 9200}])>
# streaming_bulk  [####################################]  3

# success = 3
# failed = 0
```

---

Pipe `_search` result and update `_index` with `customized handler` to do more operations before bulk!

```sh
alias jq_es_hits="jq '.hits.hits.[]'"
#
esrt r localhost -X GET /my-index-2/_search | jq_es_hits  -c | esrt t localhost -w examples.my-handlers:MyHandler # <- `examples/my-handlers.py`
# ->
# <Client([{'host': 'localhost', 'port': 9200}])>
# streaming_bulk  [####################################]  3

# success = 3
# failed = 0
```

```py
# examples/my-handlers.py
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
esrt e localhost | jq_es_hits -c
# ->
# {"_index":"my-index-2","_type":"type1","_id":"2","_score":1.0,"_source":{"field1":"22"}}
# {"_index":"new-my-index-2","_type":"type1","_id":"2","_score":1.0,"_source":{"field1":"22"}}
# {"_index":"my-index","_type":"type1","_id":"1","_score":1.0,"_source":{"field1":"cc","field2":"uu"}}
# {"_index":"my-index-2","_type":"type1","_id":"1","_score":1.0,"_source":{"field1":"11"}}
# {"_index":"new-my-index-2","_type":"type1","_id":"1","_score":1.0,"_source":{"field1":"11"}}
# {"_index":"my-index-2","_type":"type1","_id":"3","_score":1.0,"_source":{"field1":"33"}}
# {"_index":"new-my-index-2","_type":"type1","_id":"3","_score":1.0,"_source":{"field1":"33"}}
```

```sh
cat <<EOF | esrt e localhost -d - | jq_es_hits -c
{"query": {"term": {"_index": "new-my-index-2"}}}
EOF
# ->
# {"_index":"new-my-index-2","_type":"type1","_id":"2","_score":1.0,"_source":{"field1":"22"}}
# {"_index":"new-my-index-2","_type":"type1","_id":"1","_score":1.0,"_source":{"field1":"11"}}
# {"_index":"new-my-index-2","_type":"type1","_id":"3","_score":1.0,"_source":{"field1":"33"}}
```

## `s` - Search and `Scroll`

```sh
esrt s localhost
# ->
# total = 7
# {"_index": "my-index-2", "_type": "type1", "_id": "2", "_score": null, "_source": {"field1": "22"}, "sort": [0]}
# {"_index": "new-my-index-2", "_type": "type1", "_id": "2", "_score": null, "_source": {"field1": "22"}, "sort": [0]}
# {"_index": "my-index", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "cc", "field2": "uu"}, "sort": [0]}
# {"_index": "my-index-2", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "11"}, "sort": [0]}
# {"_index": "new-my-index-2", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "11"}, "sort": [0]}
# {"_index": "my-index-2", "_type": "type1", "_id": "3", "_score": null, "_source": {"field1": "33"}, "sort": [0]}
# {"_index": "new-my-index-2", "_type": "type1", "_id": "3", "_score": null, "_source": {"field1": "33"}, "sort": [0]}
```

```sh
cat <<EOF | esrt s localhost -d -
{"query": {"term": {"field1": "cc"}}}
EOF
# ->
# total = 1
# {"_index": "my-index", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "cc", "field2": "uu"}, "sort": [0]}
```

---

## Other Examples

```py
# examples/create-massive-docs.py
import json
import uuid


if __name__ == '__main__':
    for i, _ in enumerate(range(654321), start=1):
        d = {
            '_index': 'my-index-a',
            '_id': i,
            '_type': 'type1',
            '_source': {'field1': str(uuid.uuid4())},
        }
        print(json.dumps(d))
```

```sh
python examples/create-massive-docs.py | esrt t localhost -c 100000
# ->
# <Client([{'host': 'localhost', 'port': 9200}])>
# streaming_bulk  [####################################]  654321

# success = 654321
# failed = 0
```

---

```py
# examples/copy-more-docs.py
from copy import deepcopy
import json
import typing as t
import uuid


if __name__ == '__main__':
    for i, _ in enumerate(range(654321), start=1):
        d = {
            '_index': 'my-index-b',
            '_id': i,
            '_type': 'type1',
            '_source': {'field1': str(uuid.uuid4())},
        }
        print(json.dumps(d))


def handle(actions: t.Iterable[str]):
    for action in actions:
        d: dict[str, t.Any] = json.loads(action)
        yield d
        d2 = deepcopy(d)
        d2['_source']['field1'] += '!!!'
        d2['_source']['field2'] = str(uuid.uuid4())
        yield d2
```

```sh
python examples/copy-more-docs.py | esrt t localhost -w examples.copy-more-docs:handle -c 100000
# ->
# <Client([{'host': 'localhost', 'port': 9200}])>
# streaming_bulk  [####################################]  1308642

# success = 1308642
# failed = 0
```
