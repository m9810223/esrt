# esrt - Elasticsearch Request Tool

[![pypi](https://img.shields.io/pypi/v/esrt.svg)](https://pypi.python.org/pypi/esrt)

```sh
# use `pipx`
pip install pipx # install pipx
alias esrt='pipx run esrt==4.6.0'
esrt -V
```

```sh
# or use `uv`
pip install uv # install uv
alias esrt='uvx esrt@4.6.0'
esrt -V
```

## Commands

- `search`
- `scan`
- `request`
- `bulk`
<!-- - `sql` -->
- `ping`

---

## Example

You can start an es service with docker.

```sh
docker run --name "esrt-es" --rm -itd --platform=linux/amd64 -p 9200:9200 elasticsearch:5.6.9-alpine

# install sql command and restart container:
docker exec "esrt-es" elasticsearch-plugin install https://github.com/NLPchina/elasticsearch-sql/releases/download/5.6.9.0/elasticsearch-sql-5.6.9.0.zip
docker restart "esrt-es"
```

---

## `request`

Check server:

```sh
esrt request localhost -X HEAD
# ->
# true
```

Create a index:

```sh
esrt request localhost -X PUT -u /my-index
# ->
# {
#   "acknowledged": true,
#   "shards_acknowledged": true,
#   "index": "my-index"
# }
```

*If you want to `esrt` quote url path for you, add flag: `-Q`(`--quote-url`)*

Cat it:

```sh
esrt request localhost -X GET -u _cat/indices
# ->
# yellow open my-index NMHssX4qTgeMFrA3cXPoKg 5 1 0 0 324b 324b

esrt request localhost -X GET -u _cat/indices -p v=
# ->
# health status index    uuid                   pri rep docs.count docs.deleted store.size pri.store.size
# yellow open   my-index NMHssX4qTgeMFrA3cXPoKg   5   1          0            0       810b           810b

esrt request localhost -X GET -u _cat/indices -p v= -p format=json
# ->
# [
#   {
#     "health": "yellow",
#     "status": "open",
#     "index": "my-index",
#     "uuid": "NMHssX4qTgeMFrA3cXPoKg",
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

## `bulk` - Transmit data (`streaming_bulk`)

Bulk with data from file `examples/bulk.ndjson`:

```json
{ "_op_type": "index",  "_index": "my-index", "_type": "type1", "_id": "1", "field1": "ii" }
{ "_op_type": "delete", "_index": "my-index", "_type": "type1", "_id": "1" }
{ "_op_type": "create", "_index": "my-index", "_type": "type1", "_id": "1", "field1": "cc" }
{ "_op_type": "update", "_index": "my-index", "_type": "type1", "_id": "1", "doc": {"field2": "uu"} }
```

```sh
esrt bulk localhost -y -f examples/bulk.ndjson
# ->
# ⠋ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:00    4/? ?
```

---

Read payload from `stdin`. And `-d` can be omitted.

```sh
esrt bulk localhost -y <<EOF
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
EOF
# ->
# ⠋ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:00    3/? ?
```

Piping `heredoc` also works.

```sh
cat <<EOF | esrt bulk localhost -y
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
EOF
# ->
# ⠋ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:00    3/? ?
```

---

Pipe `_search` result and update `_index` with `customized handler` to do more operations before bulk!

```sh
alias jq_es_hits="jq '.hits.hits[]'"
```

```sh
esrt request localhost -X GET -u my-index-2/_search | jq_es_hits -c | esrt bulk localhost -y -w examples.my-handlers:handle  # <- `examples/my-handlers.py`
# ->
# ⠹ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:00    3/? ?
```

```py
# examples/my-handlers.py
import json
import typing as t

from esrt import DocHandler


# function style
def my_handler(actions: t.Iterable[str]):
    for action in actions:
        obj = json.loads(action)
        prefix = 'new-'
        if not t.cast(str, obj['_index']).startswith(prefix):
            obj['_index'] = prefix + obj['_index']
        yield obj


# class style
class MyHandler(DocHandler):
    def handle(self, actions: t.Iterable[str]):
        for action in actions:
            yield self.handle_one(action)

    def handle_one(self, action: str):
        obj = super().handle_one(action)
        prefix = 'new-'
        if not t.cast(str, obj['_index']).startswith(prefix):
            obj['_index'] = prefix + obj['_index']
        return obj

```

---

## `search`

```sh
esrt search localhost | jq_es_hits -c
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
esrt search localhost -f - <<EOF | jq_es_hits -c
{"query": {"term": {"_index": "new-my-index-2"}}}
EOF
# ->
# {"_index":"new-my-index-2","_type":"type1","_id":"2","_score":1.0,"_source":{"field1":"22"}}
# {"_index":"new-my-index-2","_type":"type1","_id":"1","_score":1.0,"_source":{"field1":"11"}}
# {"_index":"new-my-index-2","_type":"type1","_id":"3","_score":1.0,"_source":{"field1":"33"}}
```

## `scan`

```sh
esrt scan localhost -y
# ->
# {"_index": "my-index-2", "_type": "type1", "_id": "2", "_score": null, "_source": {"field1": "22"}, "sort": [0]}
# {"_index": "new-my-index-2", "_type": "type1", "_id": "2", "_score": null, "_source": {"field1": "22"}, "sort": [0]}
# {"_index": "my-index", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "cc", "field2": "uu"}, "sort": [0]}
# {"_index": "my-index-2", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "11"}, "sort": [0]}
# {"_index": "new-my-index-2", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "11"}, "sort": [0]}
# {"_index": "my-index-2", "_type": "type1", "_id": "3", "_score": null, "_source": {"field1": "33"}, "sort": [0]}
# {"_index": "new-my-index-2", "_type": "type1", "_id": "3", "_score": null, "_source": {"field1": "33"}, "sort": [0]}

```

```sh
esrt scan localhost -y -f - <<EOF
{"query": {"term": {"field1": "cc"}}}
EOF
# ->
# {"_index": "my-index", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "cc", "field2": "uu"}, "sort": [0]}

```

<!--
## `sql` - Elasticsearch SQL

```sh
# Elasticsearch v6
export ESRT_SQL_API=_xpack/sql
```

```sh
esrt sql localhost -f - <<EOF | jq_es_hits -c
SELECT * from new-my-index-2
EOF
# ->
# {"_index":"new-my-index-2","_type":"type1","_id":"2","_score":1.0,"_source":{"field1":"22"}}
# {"_index":"new-my-index-2","_type":"type1","_id":"1","_score":1.0,"_source":{"field1":"11"}}
# {"_index":"new-my-index-2","_type":"type1","_id":"3","_score":1.0,"_source":{"field1":"33"}}
```
-->

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
python examples/create-massive-docs.py | tee -a _.ndjson | esrt bulk localhost -y -c 10000
# ->
# ⠋ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:26    654321/? 24504/s

cat _.ndjson  # <- 79M

head _.ndjson
# ->
# {"_index": "my-index-a", "_type": "type1", "_id": "70004", "_score": null, "_source": {"field1": "7fc553c1-d09f-4793-bc28-2a16a6050ef4"}, "sort": [0]}
# {"_index": "my-index-a", "_type": "type1", "_id": "80002", "_score": null, "_source": {"field1": "7fddf2f7-195f-4964-81f1-bb32d63be8b0"}, "sort": [0]}
# {"_index": "my-index-2", "_type": "type1", "_id": "2", "_score": null, "_source": {"field1": "22"}, "sort": [0]}
# {"_index": "my-index-a", "_type": "type1", "_id": "70003", "_score": null, "_source": {"field1": "2a08f0e0-cdbd-47d3-b7e3-ee8fd1e27ff8"}, "sort": [0]}
# {"_index": "new-my-index-2", "_type": "type1", "_id": "2", "_score": null, "_source": {"field1": "22"}, "sort": [0]}
# {"_index": "my-index", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "cc", "field2": "uu"}, "sort": [0]}
# {"_index": "my-index-2", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "11"}, "sort": [0]}
# {"_index": "new-my-index-2", "_type": "type1", "_id": "1", "_score": null, "_source": {"field1": "11"}, "sort": [0]}
# {"_index": "my-index-2", "_type": "type1", "_id": "3", "_score": null, "_source": {"field1": "33"}, "sort": [0]}
# {"_index": "new-my-index-2", "_type": "type1", "_id": "3", "_score": null, "_source": {"field1": "33"}, "sort": [0]}

```

---

```py
# examples/copy-more-docs.py
from copy import deepcopy
import json
import typing as t
import uuid


if __name__ == '__main__':
    for i, _ in enumerate(range(54321), start=1):
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
python examples/copy-more-docs.py | esrt bulk localhost -y -w examples.copy-more-docs:handle
# ->
# ⠏ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:05    108642/? 18963/s
```
