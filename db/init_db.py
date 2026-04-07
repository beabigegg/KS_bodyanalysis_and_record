from __future__ import annotations

import argparse
from pathlib import Path
import sys

from sqlalchemy import create_engine

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from db.schema import metadata


def init_db() -> None:
    settings = load_settings()
    engine = create_engine(settings.mysql.sqlalchemy_url(), future=True)
    metadata.create_all(engine)


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize recipe parser database tables.")
    parser.add_argument(
        "--config",
        help="Deprecated and ignored. Settings are loaded from environment variables.",
    )
    args = parser.parse_args()
    _ = args.config
    init_db()


if __name__ == "__main__":
    main()
