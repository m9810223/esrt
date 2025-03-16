from .cmd_base import BaseCmd
from .cmd_base import DocTypeCmdMixin
from .cmd_base import IndexCmdMixin
from .cmd_base import ParamsCmdMixin
from .cmd_base import PrettyCmdMixin
from .cmd_base import SearchFioCmdMixin


class RequestCmd(SearchFioCmdMixin, IndexCmdMixin, DocTypeCmdMixin, ParamsCmdMixin, PrettyCmdMixin, BaseCmd):
    def cli_cmd(self) -> None:
        pass
