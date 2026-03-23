from __future__ import annotations

import argparse
from pathlib import Path
import sys

from sqlalchemy import create_engine

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from db.schema import metadata


def init_db(config_path: str = "config.yaml") -> None:
    settings = load_settings(config_path)
    engine = create_engine(settings.mysql.sqlalchemy_url(), future=True)
    metadata.create_all(engine)


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize recipe parser database tables.")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML.")
    args = parser.parse_args()
    init_db(args.config)


if __name__ == "__main__":
    main()
