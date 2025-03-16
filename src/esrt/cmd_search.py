from .cmd_base import BaseEsCmd
from .cmd_base import DefaultPrettyCmdMixin
from .cmd_base import EsDocTypeCmdMixin
from .cmd_base import EsIndexCmdMixin
from .cmd_base import EsParamsCmdMixin
from .cmd_base import JsonInputCmdMixin
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console


class SearchCmd(
    JsonInputCmdMixin, EsIndexCmdMixin, EsDocTypeCmdMixin, EsParamsCmdMixin, DefaultPrettyCmdMixin, BaseEsCmd
):
    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_console.print(self)

        if self.verbose:
            stderr_dim_console.print('>', end='')

        body = self.read_json_input()

        if self.verbose and not self.is_input_stdin:
            stderr_console.print_json(self._to_json_str(body))

        if self.verbose:
            stderr_dim_console.print('<', end='')

        response = self.client.search(
            index=self.index,
            doc_type=self.doc_type,
            body=body,
            params=self.params,
        )

        line = self._to_json_str(response)

        if self.pretty:
            self.output.print_json(line)
        else:
            self.output.print_json(line, indent=None)
