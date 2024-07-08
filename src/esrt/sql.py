from enum import Enum


class SqlUrlEnum(str, Enum):
    default = '_sql'
    v6 = '_xpack/sql'
    nlpcn = '_nlpcn/sql'  # https://github.com/NLPchina/elasticsearch-sql

    @classmethod
    def values(cls):
        return [x.value for x in cls._member_map_.values()]
