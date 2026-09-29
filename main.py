# main.py  (프로젝트 루트)
import sys
from budget_app.cli import CLI
from budget_app import cli


def main() -> None:
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "./data"
    app = CLI(data_dir=data_dir)
    app.run()


if __name__ == "__main__":
    main()