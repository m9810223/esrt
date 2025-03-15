import logging

from rich.console import Console
from rich.logging import RichHandler


logger = logging.getLogger('esrt')


def set_log_level(level: str) -> None:
    logging.basicConfig(
        format='{message}',
        datefmt='%X.%f',
        style='{',
        level=level,
        handlers=[
            RichHandler(
                console=Console(stderr=True),
                omit_repeated_times=False,
                show_path=False,
            )
        ],
    )
