import logging
import sys

import typer


logger = logging.getLogger('esrt')


def set_log_level(level: str):
    logging.basicConfig(
        format=typer.style('{levelname:<7} ' '[{asctime}] ' '{message} ', dim=True),
        datefmt='%H:%M:%S',
        style='{',
        level=level,
        handlers=[logging.StreamHandler(sys.stderr)],
    )
