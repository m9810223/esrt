import logging
import sys


logger = logging.getLogger('esrt')


def set_log_level(level: str):
    logging.basicConfig(
        format='{levelname:<7} ' '[{asctime}] ' '{message} ',
        datefmt='%H:%M:%S',
        style='{',
        level=level,
        handlers=[logging.StreamHandler(sys.stderr)],
    )
