from pydantic_settings import CliImplicitFlag

from .cmd_base import BaseCmd
from .cmd_base import DocTypeCmdMixin
from .cmd_base import IndexCmdMixin
from .cmd_base import ParamsCmdMixin
from .cmd_base import SearchFioCmdMixin
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console

from .cmd_base import stderr_dim_console, PrettyCmdMixin


class RequestCmd(SearchFioCmdMixin, IndexCmdMixin, DocTypeCmdMixin, ParamsCmdMixin, PrettyCmdMixin, BaseCmd):
    def cli_cmd(self) -> None:
        pass
