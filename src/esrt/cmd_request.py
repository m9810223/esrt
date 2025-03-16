from .cmd_base import BaseEsCmd
from .cmd_base import DefaultPrettyCmdMixin
from .cmd_base import EsDocTypeCmdMixin
from .cmd_base import EsIndexCmdMixin
from .cmd_base import EsParamsCmdMixin
from .cmd_base import JsonInputCmdMixin


class RequestCmd(
    JsonInputCmdMixin, EsIndexCmdMixin, EsDocTypeCmdMixin, EsParamsCmdMixin, DefaultPrettyCmdMixin, BaseEsCmd
):
    def cli_cmd(self) -> None:
        pass
