from pprint import pformat

from elasticsearch import Elasticsearch

from .logging_ import logger


class Client(Elasticsearch):
    def __init__(self, *, host: str) -> None:
        has_scheme = '://' in host
        has_port = ':' in host.split('://')[-1].split('@')[-1]
        if (not has_scheme) and (not has_port):
            host += ':9200'
        super().__init__(hosts=host)
        logger.warning(pformat(self.transport.hosts))
