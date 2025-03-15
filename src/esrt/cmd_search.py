import json

from .cmd_base import BaseCmd
from .cmd_base import DocTypeCmdMixin
from .cmd_base import FioCmdMixin
from .cmd_base import IndexCmdMixin
from .cmd_base import ParamsCmdMixin
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console


class SearchCmd(FioCmdMixin, IndexCmdMixin, DocTypeCmdMixin, ParamsCmdMixin, BaseCmd):
    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_dim_console.print(self)

        if self.verbose:
            stderr_dim_console.out('>', end='')
            stderr_console.print_json(json.dumps(self.input_), ensure_ascii=True)

        if self.verbose:
            stderr_dim_console.out('<', end='')

        response = self.client.search(
            index=self.index,
            doc_type=self.doc_type,
            body=self.input_,
            params=self.params,
        )

        line = self._to_line(response)

        self.output.print_json(line)
