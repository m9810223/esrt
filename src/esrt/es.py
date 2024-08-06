from elasticsearch import Elasticsearch


class Client(Elasticsearch):
    def __init__(self, *, host: str):
        super().__init__(hosts=host)
