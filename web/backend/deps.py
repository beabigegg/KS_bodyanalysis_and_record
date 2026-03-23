from __future__ import annotations

import sys
from pathlib import Path
from typing import Generator

from sqlalchemy import Connection, Engine, create_engine

from config import settings

# Let backend reuse root project modules such as db/schema.py.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.schema import metadata  # noqa: E402


engine: Engine = create_engine(
    settings.mysql_url,
    future=True,
    pool_pre_ping=True,
)


def get_connection() -> Generator[Connection, None, None]:
    with engine.connect() as conn:
        yield conn


__all__ = ["engine", "get_connection", "metadata"]

