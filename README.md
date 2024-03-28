# esrt - Elasticsearch Request Tool

[![pypi](https://img.shields.io/pypi/v/esrt.svg)](https://pypi.python.org/pypi/esrt)

```sh
pip install pipx
pipx install esrt -f
```

## Example

You can start an es service with docker.

```sh
docker run --rm -it --platform=linux/amd64 -p 9200:9200 elasticsearch:5.6.9-alpine
```

---

## `r` - Send a request

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
# [{"health": "yellow", "status": "open", "index": "my-index", "uuid": "FQjeEOKQT8aroL2dgO7yDg", "pri": "5", "rep": "1", "docs.count": "0", "docs.deleted": "0", "store.size": "324b", "pri.store.size": "324b"}]
```

*Note: `esrt` doesn't keep `-p pretty` format by default, but you can use `jq` instead.*

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

Bulk with data from file `dev.ndjson`:

```json
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
#
# success = 0
# failed = 0
```

---

Pipe `_search` result and update `_index` with `customized handler` to do more operations before bulk!

```sh
alias jq_es_hits="jq '.hits.hits.[]' -c"
#
esrt r localhost -X GET /my-index/_search | jq_es_hits | esrt t localhost -w dev:MyHandler # <- `examples/my-handlers.py`
# ->
# <Client([{'host': 'localhost', 'port': 9200}])>
# streaming_bulk  [####################################]  1
#
# success = 0
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

---

## Other Examples

```sh
python examples/create-massive-docs.py | esrt t localhost
```

```py
# examples/create-massive-docs.py
import json
from random import choices
from string import ascii_letters


def main():
    for i in range(1, 2222):
        d = {
            '_index': 'my-index-a',
            '_id': i,
            '_type': 'type1',
            '_source': {'field1': ''.join(choices(ascii_letters, k=8))},
        }
        print(json.dumps(d))


if __name__ == '__main__':
    main()
```

---

```sh
python examples/copy-more-docs.py | esrt t localhost -w examples.copy-more-docs:handle
```

```py
# examples/copy-more-docs.py
from copy import deepcopy
import json
from random import choices
from string import ascii_letters
import typing as t


def handle(actions: t.Iterable[str]):
    for action in actions:
        d: dict[str, t.Any] = json.loads(action)
        yield d
        d2 = deepcopy(d)
        d2['_source']['field1'] += '!!!'
        d2['_source']['field2'] = ''.join(choices(ascii_letters, k=8))
        yield d2


def main():
    for i in range(1, 2222):
        d = {
            '_index': 'my-index-b',
            '_id': i,
            '_type': 'type1',
            '_source': {'field1': ''.join(choices(ascii_letters, k=8))},
        }
        print(json.dumps(d))


if __name__ == '__main__':
    main()
```
