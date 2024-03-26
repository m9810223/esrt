import json
from pathlib import Path
import typing as t

from esrt import ActionHandler


def my_handler(actions: t.Iterable[str]):
    for action in actions:
        yield json.loads(action)


class MyHandler(ActionHandler):
    def handle_one(self, action: str):
        obj = json.loads(action)
        prefix = 'new-'
        if not t.cast(str, obj['_index']).startswith(prefix):
            self.print(f'prefixing {obj["_index"]!r}')
            obj['_index'] = prefix + obj['_index']
        return obj


if __name__ == '__main__':
    search_body = {
        'query': {
            'bool': {
                # [scored: O]
                'filter': [  # `and`
                    {'term': {'itemTimestamp': 1707006570}},
                    {'terms': {'itemTimestamp': [1707006570]}},
                    {
                        'range': {
                            'itemTimestamp': {
                                'gte': 1707006569,
                                'lte': 1707006570,
                            }
                        }
                    },
                ],
                # [scored: X]
                'must': [  # `and`
                    #
                ],
                'must_not': [],  # `not`
                'should': [  # `or`
                    #
                ],
            },
        },
    }
    print(
        json.dumps(search_body, ensure_ascii=False, indent=2),
        end='',
        file=Path('__.conf.json').open('w'),
    )
