from .cmd_base import BaseCmd
from .cmd_base import DocTypeCmdMixin
from .cmd_base import FioCmdMixin
from .cmd_base import IndexCmdMixin
from .cmd_base import ParamsCmdMixin
from .cmd_base import stderr_dim_console


class ScanCmd(
    FioCmdMixin,
    IndexCmdMixin,
    DocTypeCmdMixin,
    ParamsCmdMixin,
    BaseCmd,
):
    scroll: str = '5m'

    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_dim_console.print(self)

        for hit in self.client.scan(
            query=self.input_,
            scroll=self.scroll,
            index=self.index,
            doc_type=self.doc_type,
        ):
            line = self._to_json_str(hit)

            self.output.out(line)

            if not self.is_output_stdout:
                stderr_dim_console.print(line)
