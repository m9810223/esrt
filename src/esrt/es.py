from elasticsearch import Elasticsearch


class Client(Elasticsearch):
    def __init__(self, *, host: str):
        is_https = host.startswith('https://')
        has_port = ':' in host.split('://')[-1]
        if not is_https:
            if not has_port:
                host += ':9200'
        super().__init__(hosts=host)
