# esrt - Elasticsearch Request Tool

[![pypi](https://img.shields.io/pypi/v/esrt.svg)](https://pypi.python.org/pypi/esrt)

## CLI

```sh
pipx install esrt
```

---

## `e` - search

```sh
esrt e localhost -d e.json
```

`e.json`:

```json
{
  "_source": [],
  "size": 1,
  "query": {
    "bool": {
      "filter": [
        {
          "term": {
            "_index": "my-index"
          }
        }
      ],
      "must": [],
      "must_not": [],
      "should": []
    }
  }
}
```

```sh
esrt e localhost | jq '.hits.hits.[] | . + ._source | del(._source)' -c
```

## `s` - scan, source

```sh
cat <<EOF | esrt s localhost -d - | jq -c
{
  "query": {
    "bool": {
      "filter": [
        {
          "terms": {
            "itemTimestamp": [
              1707006570
            ]
          }
        }
      ]
    }
  }
}
EOF
```

## `r` - perform_request (request path)

```sh
cat <<EOF | esrt r localhost -X POST _sql -d -
SELECT * FROM my-index
EOF
```

```sh
esrt r localhost -X GET _cat/indices -p 'pretty=&format=json&v&s=index' | jq
```

## `t` - streaming_bulk (bulk) / target

```sh
esrt s localhost -d __.conf.json | esrt t localhost -d - | jq -c
```

```py
# dev.py
import json
import typing as t

from esrt import ActionHandler

class MyHandler(ActionHandler):
    def handle_one(self, action: str):
        obj = json.loads(action)
        prefix = 'new-'
        if not t.cast(str, obj['_index']).startswith(prefix):
            self.print(f'prefixing {obj["_index"]!r}')
            obj['_index'] = prefix + obj['_index']
        return obj
```

```sh
esrt s localhost -d __.conf.json | esrt t localhost -d - -w dev:MyHandler | jq -c
```
