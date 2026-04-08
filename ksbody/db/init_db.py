from __future__ import annotations

import argparse

from sqlalchemy import Engine, create_engine

from ksbody.config import get_settings
from ksbody.db.schema import metadata


def ensure_schema(engine: Engine | None = None) -> Engine:
    if engine is None:
        settings = get_settings()
        engine = create_engine(settings.mysql.sqlalchemy_url(), future=True)
    metadata.create_all(engine)
    return engine


def init_db() -> None:
    ensure_schema()


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
