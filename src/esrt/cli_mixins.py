import typer
from typer.core import TyperGroup


# https://github.com/tiangolo/typer/issues/132#issuecomment-1714516903
class AliasGroupMixin(TyperGroup):
    def get_command(self, ctx: typer.Context, cmd_name: str):
        for cmd in self.commands.values():
            if cmd.name and cmd_name in [x.strip() for x in cmd.name.split('/')]:
                cmd_name = cmd.name
                break
        return super().get_command(ctx, cmd_name)


# https://github.com/tiangolo/typer/issues/428#issuecomment-1238866548
class OrderGroupMixin(TyperGroup):
    def list_commands(self, ctx: typer.Context):
        return list(self.commands)
