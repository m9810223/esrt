import typing as t

from pydantic import AliasChoices
from pydantic import Field
from pydantic import JsonValue
from pydantic_settings import CliImplicitFlag

from .cmd_base import BaseEsCmd
from .cmd_base import ConfirmCmdMixin
from .cmd_base import DefaultNoPrettyCmdMixin
from .cmd_base import DryRunCmdMixin
from .cmd_base import EsDocTypeCmdMixin
from .cmd_base import EsIndexCmdMixin
from .cmd_base import EsParamsCmdMixin
from .cmd_base import IpythonCmdMixin
from .cmd_base import JsonInputCmdMixin
from .cmd_base import rich_text
from .cmd_base import stderr_console
from .cmd_base import stderr_dim_console
from .typealiases import JsonBodyT


class ScanCmd(
    IpythonCmdMixin,
    ConfirmCmdMixin,
    JsonInputCmdMixin,
    EsIndexCmdMixin,
    EsDocTypeCmdMixin,
    EsParamsCmdMixin,
    DryRunCmdMixin,
    DefaultNoPrettyCmdMixin,
    BaseEsCmd,
):
    scroll: str = '5m'
    raise_on_error: CliImplicitFlag[bool] = Field(
        default=True,
        validation_alias=AliasChoices(
            'e',
            'raise',
            'raise_on_error',
        ),
        description=rich_text('[b blue]Raises an exception if an error is encountered (some shards fail to execute).'),
    )
    preserve_order: t.ClassVar[bool] = False
    size: int = Field(
        default=1000,
        lt=10000,
        validation_alias=AliasChoices(
            'N',
            'size',
        ),
        description=rich_text('[b blue]Size (per shard) of the batch send at each iteration.'),
    )
    request_timeout: t.Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices(
            't',
            'request_timeout',
        ),
        description=rich_text('[b blue]Explicit timeout for each call to scan.'),
    )
    clear_scroll: t.ClassVar[bool] = True
    scroll_kwargs: dict[str, JsonValue] = Field(
        default_factory=dict,
        validation_alias=AliasChoices(
            'k',
            'scroll_kwargs',
        ),
        description=rich_text('[b blue]Additional kwargs to be passed to `Elasticsearch.scroll`'),
    )

    def _preview_total(self, query: t.Optional[JsonBodyT], /) -> int:
        with stderr_console.status('Search ... (total)') as status:
            status.update(spinner='bouncingBall')

            search_once = self.client.search(
                index=self.index,
                doc_type=self.doc_type,
                body=query,
                params={**self.params, 'size': 0},
            )

        total = t.cast(dict, search_once)['hits']['total']
        return total

    def cli_cmd(self) -> None:  # noqa: C901
        if (not self.dry_run) and (not self.confirm()):
            return

        if self.verbose:
            stderr_dim_console.print(self)

        query = self.read_json_input()

        items = self.client.scan(
            query=query,
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

        total = self._preview_total(query)

        if self.dry_run:
            stderr_console.print('Total:', total, style='b yellow')
            return

        if self.is_output_stdout:
            for item in items:
                if self.pretty:
                    self.output.print_json(data=item)
                else:
                    self.output.print_json(data=item, indent=None)

            return

        with self.progress(console=stderr_console, title='scan') as progress:
            for item in progress.track(items, total=total):
                self.output.out(self.json_to_str(item))

                if self.verbose:
                    if self.pretty:
                        stderr_dim_console.print_json(data=item)
                    else:
                        stderr_dim_console.print_json(data=item, indent=None)

                    progress.refresh()

        if self.ipython:
            self.start_ipython()
