import typing as t

from pydantic import AfterValidator
from pydantic import AliasChoices
from pydantic import Field
from rich.text import Text

from .cmd_base import BaseEsCmd
from .cmd_base import BaseInputCmdMixin
from .cmd_base import EsHeadersCmdMixin
from .cmd_base import EsParamsCmdMixin
from .cmd_base import json_body_type_adapter
from .cmd_base import rich_text
from .typealiases import HttpMethod


class RequestCmd(BaseInputCmdMixin, EsHeadersCmdMixin, EsParamsCmdMixin, BaseEsCmd):
    method: t.Annotated[HttpMethod, AfterValidator(str.upper)] = Field(
        default='GET',
        validation_alias=AliasChoices(
            'X',
            'method',
            'request',
        ),
    )
    url: str = Field(
        validation_alias=AliasChoices(
            'u',
            'url',
        ),
        description=rich_text(
            Text('Absolute url (without host) to target', style='blue b'),
        ),
    )

    def cli_cmd(self) -> None:
        s = None if self.input_ is None else (self.input_.read().strip() or None)
        body = None if s is None else json_body_type_adapter.validate_python(s)
        response = self.client.request(
            method=self.method,
            url=self.url,
            headers=self.headers,
            params=self.params,
            body=body,
        )
        print(response)
