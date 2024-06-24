from pathlib import Path
import sys

from .cli import app


def main():
    sys.path.insert(0, str(Path.cwd()))
    app()


if __name__ == '__main__':
    main()
