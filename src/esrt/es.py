from elasticsearch import Elasticsearch


class Client(Elasticsearch):
    def __init__(self, *, host: str):
        if not host.startswith('http'):
            host = 'http://' + host
        if ':' not in host.split('://')[-1]:
            host += ':9200'
        super().__init__(hosts=host)
