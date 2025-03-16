# esrt - Elasticsearch Request Tool

[![pypi](https://img.shields.io/pypi/v/esrt.svg)](https://pypi.python.org/pypi/esrt)

```sh
# use `pipx`
pip install pipx # install pipx
alias esrt='pipx run esrt==4.1.3'
esrt -V
```

```sh
# or use `uv`
pip install uv # install uv
alias esrt='uvx esrt@4.1.3'
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
# yellow open my-index Ya31jYWMQVW0o_-IosLoNQ 5 1 0 0 810b 810b

esrt request localhost -X GET -u _cat/indices -p v=
# ->
# health status index    uuid                   pri rep docs.count docs.deleted store.size pri.store.size
# yellow open   my-index Ya31jYWMQVW0o_-IosLoNQ   5   1          0            0       810b           810b

esrt request localhost -X GET -u _cat/indices -p v= -p format=json
# ->
# [
#   {
#     "health": "yellow",
#     "status": "open",
#     "index": "my-index",
#     "uuid": "Ya31jYWMQVW0o_-IosLoNQ",
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
esrt bulk localhost -f examples/bulk.ndjson -y
# ->
# verbose=False output=<console width=227 ColorSystem.TRUECOLOR> client=<Client([{'host': 'localhost'}])> pretty=False dry_run=False params={} doc_type=None index=None input_=<_io.TextIOWrapper name='examples/bulk.ndjson' mode='r' encoding='UTF-8'> yes=True handler=<function doc_handler at 0x104397c10> chunk_size=5000 max_chunk_bytes=104857600 raise_on_error=True raise_on_exception=True max_retries=5 initial_backoff=3 max_backoff=600 yield_ok=True
# ⠋ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:00    4/? ?
# {"index": {"_index": "my-index", "_type": "type1", "_id": "1", "_version": 1, "result": "created", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": true, "status": 201}}
# {"delete": {"found": true, "_index": "my-index", "_type": "type1", "_id": "1", "_version": 2, "result": "deleted", "_shards": {"total": 2, "successful": 1, "failed": 0}, "status": 200}}
# {"create": {"_index": "my-index", "_type": "type1", "_id": "1", "_version": 3, "result": "created", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": true, "status": 201}}
# {"update": {"_index": "my-index", "_type": "type1", "_id": "1", "_version": 4, "result": "updated", "_shards": {"total": 2, "successful": 1, "failed": 0}, "status": 200}}
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
# verbose=False output=<console width=227 ColorSystem.TRUECOLOR> client=<Client([{'host': 'localhost'}])> pretty=False dry_run=False params={} doc_type=None index=None input_=<_io.TextIOWrapper name='<stdin>' mode='r' encoding='utf-8'> yes=True handler=<function doc_handler at 0x1042bfc10> chunk_size=5000 max_chunk_bytes=104857600 raise_on_error=True raise_on_exception=True max_retries=5 initial_backoff=3 max_backoff=600 yield_ok=True
# ⠋ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:00    3/? ?
# {"index": {"_index": "my-index-2", "_type": "type1", "_id": "1", "_version": 1, "result": "created", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": true, "status": 201}}
# {"index": {"_index": "my-index-2", "_type": "type1", "_id": "2", "_version": 1, "result": "created", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": true, "status": 201}}
# {"index": {"_index": "my-index-2", "_type": "type1", "_id": "3", "_version": 1, "result": "created", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": true, "status": 201}}

```

Piping `heredoc` also works.

```sh
cat <<EOF | esrt bulk localhost -y
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "1", "field1": "11" }
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "2", "field1": "22" }
{ "_op_type": "index",  "_index": "my-index-2", "_type": "type1", "_id": "3", "field1": "33" }
EOF
# ->
# verbose=False output=<console width=227 ColorSystem.TRUECOLOR> client=<Client([{'host': 'localhost'}])> pretty=False dry_run=False params={} doc_type=None index=None input_=<_io.TextIOWrapper name='<stdin>' mode='r' encoding='utf-8'> yes=True handler=<function doc_handler at 0x102c1bc10> chunk_size=5000 max_chunk_bytes=104857600 raise_on_error=True raise_on_exception=True max_retries=5 initial_backoff=3 max_backoff=600 yield_ok=True
# ⠋ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:00    3/? ?
# {"index": {"_index": "my-index-2", "_type": "type1", "_id": "1", "_version": 2, "result": "updated", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": false, "status": 200}}
# {"index": {"_index": "my-index-2", "_type": "type1", "_id": "2", "_version": 2, "result": "updated", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": false, "status": 200}}
# {"index": {"_index": "my-index-2", "_type": "type1", "_id": "3", "_version": 2, "result": "updated", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": false, "status": 200}}
```

---

Pipe `_search` result and update `_index` with `customized handler` to do more operations before bulk!

```sh
alias jq_es_hits="jq '.hits.hits[]'"
```

```sh
esrt request localhost -X GET -u my-index-2/_search | jq_es_hits -c | esrt bulk localhost -y -w examples.my-handlers:MyHandler  # <- `examples/my-handlers.py`
# ->
# verbose=False output=<console width=227 ColorSystem.TRUECOLOR> client=<Client([{'host': 'localhost'}])> pretty=False dry_run=False params={} doc_type=None index=None input_=<_io.TextIOWrapper name='<stdin>' mode='r' encoding='utf-8'> yes=True handler=<class 'examples.my-handlers.MyHandler'> chunk_size=5000 max_chunk_bytes=104857600 raise_on_error=True raise_on_exception=True max_retries=5 initial_backoff=3 max_backoff=600 yield_ok=True
# ⠋ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:00    3/? ?
# {"index": {"_index": "new-my-index-2", "_type": "type1", "_id": "2", "_version": 6, "result": "updated", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": false, "status": 200}}
# {"index": {"_index": "new-my-index-2", "_type": "type1", "_id": "1", "_version": 6, "result": "updated", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": false, "status": 200}}
# {"index": {"_index": "new-my-index-2", "_type": "type1", "_id": "3", "_version": 6, "result": "updated", "_shards": {"total": 2, "successful": 1, "failed": 0}, "created": false, "status": 200}}
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
# verbose=False output=<console width=227 ColorSystem.TRUECOLOR> client=<Client([{'host': 'localhost'}])> pretty=False params={} doc_type=None index=None input_=None yes=True scroll='5m' raise_on_error=True size=1000 request_timeout=None scroll_kwargs={}
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
# verbose=False output=<console width=227 ColorSystem.TRUECOLOR> client=<Client([{'host': 'localhost'}])> pretty=False params={} doc_type=None index=None input_=<_io.TextIOWrapper name='<stdin>' mode='r' encoding='utf-8'> yes=True scroll='5m' raise_on_error=True size=1000 request_timeout=None scroll_kwargs={}
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
# <Client([{'host': 'localhost', 'port': 9200}])>
# streaming_bulk  [####################################]  654321

# success = 654321
# failed = 0

cat _.ndjson  # <- 79M
# ->
# {"_index": "my-index-a", "_id": 1, "_type": "type1", "_source": {"field1": "7e6a3924-1258-4e44-a19b-15395e802b1b"}}
# {"_index": "my-index-a", "_id": 2, "_type": "type1", "_source": {"field1": "9a05ea11-349b-452f-b771-a1aa168bdca9"}}
# {"_index": "my-index-a", "_id": 3, "_type": "type1", "_source": {"field1": "2e4d2d6a-54e3-4160-adbb-d0c52759bb89"}}
# {"_index": "my-index-a", "_id": 4, "_type": "type1", "_source": {"field1": "72cbc979-ed03-4653-8bb6-9f3dd723a2c8"}}
# {"_index": "my-index-a", "_id": 5, "_type": "type1", "_source": {"field1": "61a0acce-e415-4ac7-8417-66ccfe0f7932"}}
# {"_index": "my-index-a", "_id": 6, "_type": "type1", "_source": {"field1": "ba84e4b9-881c-4042-bf39-a449766f9e4b"}}
# {"_index": "my-index-a", "_id": 7, "_type": "type1", "_source": {"field1": "e92b2d83-97ae-4d5e-9797-b9ade4841f87"}}
# {"_index": "my-index-a", "_id": 8, "_type": "type1", "_source": {"field1": "c36acdb2-ea4e-4716-ad16-166171fa181d"}}
# {"_index": "my-index-a", "_id": 9, "_type": "type1", "_source": {"field1": "f17d588b-cbd0-4f72-8a47-040eb1203e35"}}
# {"_index": "my-index-a", "_id": 10, "_type": "type1", "_source": {"field1": "ac5d00fd-6443-4380-8d1b-72595d3f890c"}}
# {"_index": "my-index-a", "_id": 11, "_type": "type1", "_source": {"field1": "5d997ac9-e2c0-4347-9415-9d981f40f856"}}
# {"_index": "my-index-a", "_id": 12, "_type": "type1", "_source": {"field1": "7cf7ef75-9d95-4736-851b-5099dd11d1d6"}}
# {"_index": "my-index-a", "_id": 13, "_type": "type1", "_source": {"field1": "a7db50d4-65da-499f-84d2-5e27f719b3a7"}}
# {"_index": "my-index-a", "_id": 14, "_type": "type1", "_source": {"field1": "fd48cc37-520c-41be-a3e4-6e242bf91fed"}}
# {"_index": "my-index-a", "_id": 15, "_type": "type1", "_source": {"field1": "767286bb-5590-4265-b6f5-ce789f5f2848"}}
# {"_index": "my-index-a", "_id": 16, "_type": "type1", "_source": {"field1": "eca18f61-8189-46bc-b455-520a5c0a26d3"}}
# {"_index": "my-index-a", "_id": 17, "_type": "type1", "_source": {"field1": "61508630-c2b2-4f93-a91b-056c69208c34"}}
# {"_index": "my-index-a", "_id": 18, "_type": "type1", "_source": {"field1": "c6f1df60-9652-4102-98f8-df3c3e5d966b"}}
# {"_index": "my-index-a", "_id": 19, "_type": "type1", "_source": {"field1": "63c85746-baea-4fc5-a3c1-2638c2d3b9ed"}}
# {"_index": "my-index-a", "_id": 20, "_type": "type1", "_source": {"field1": "bd47ee1f-198c-4da8-8c3d-458814d547b9"}}
# ......
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
# verbose=False output=<console width=227 ColorSystem.TRUECOLOR> client=<Client([{'host': 'localhost'}])> pretty=False dry_run=False params={} doc_type=None index=None input_=<_io.TextIOWrapper name='<stdin>' mode='r' encoding='utf-8'> yes=True handler=<function handle at 0x1037fe160> chunk_size=5000 max_chunk_bytes=104857600 raise_on_error=True raise_on_exception=True max_retries=5 initial_backoff=3 max_backoff=600 yield_ok=False
# ⠸ bulk ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:03    108642/? 30680/s
```
