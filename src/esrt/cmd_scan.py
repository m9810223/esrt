import typing as t

from pydantic import AliasChoices
from pydantic import Field
from pydantic import JsonValue
from pydantic_settings import CliImplicitFlag
from rich.text import Text

from .cmd_base import BaseCmd
from .cmd_base import DocTypeCmdMixin
from .cmd_base import IndexCmdMixin
from .cmd_base import ParamsCmdMixin
from .cmd_base import SearchFioCmdMixin
from .cmd_base import rich_text
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console


class ScanCmd(
    SearchFioCmdMixin,
    IndexCmdMixin,
    DocTypeCmdMixin,
    ParamsCmdMixin,
    BaseCmd,
):
    scroll: str = '5m'
    raise_on_error: CliImplicitFlag[bool] = Field(
        default=True,
        validation_alias=AliasChoices(
            'e',
            'raise',
            'raise_on_error',
        ),
        description=rich_text(
            Text(
                'Raises an exception if an error is encountered (some shards fail to execute).',
                style='blue b',
            ),
        ),
    )
    preserve_order: t.ClassVar[bool] = False
    size: int = Field(
        default=1000,
        validation_alias=AliasChoices(
            'N',
            'size',
        ),
        description=rich_text(
            Text('Size (per shard) of the batch send at each iteration.', style='blue b'),
        ),
    )
    request_timeout: t.Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices(
            't',
            'request_timeout',
        ),
        description=rich_text(
            Text('Explicit timeout for each call to scan.', style='blue b'),
        ),
    )
    clear_scroll: t.ClassVar[bool] = True
    scroll_kwargs: dict[str, JsonValue] = Field(
        default_factory=dict,
        validation_alias=AliasChoices(
            'k',
            'scroll_kwargs',
        ),
        description=rich_text(
            Text('Additional kwargs to be passed to `Elasticsearch.scroll`', style='blue b'),
        ),
    )

    def cli_cmd(self) -> None:
        if self.verbose:
            stderr_dim_console.print(self)

        items = self.client.scan(
            query=self.input_,
            scroll=self.scroll,
            raise_on_error=self.raise_on_error,
            preserve_order=self.preserve_order,
            size=self.size,
            request_timeout=self.request_timeout,
            clear_scroll=self.clear_scroll,
            scroll_kwargs=self.scroll_kwargs,
            #
            index=self.index,
            doc_type=self.doc_type,
            params=self.params,
        )

        if self.is_output_stdout:
            for item in items:
                line = self._to_json_str(item)
                self.output.out(line)

            return

        with self._progress(console=stderr_console, title='bulk') as progress:
            for item in progress.track(items):
                line = self._to_json_str(item)
                self.output.out(line)

                stderr_console.print(line)
