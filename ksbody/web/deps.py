from __future__ import annotations

from typing import Generator

from sqlalchemy import Connection, Engine, create_engine

from ksbody.config import get_settings

settings = get_settings()

from ksbody.db.schema import metadata


engine: Engine = create_engine(
    settings.mysql.sqlalchemy_url(),
    future=True,
    pool_pre_ping=True,
)


def get_connection() -> Generator[Connection, None, None]:
    with engine.connect() as conn:
        yield conn


def get_writable_connection() -> Generator[Connection, None, None]:
    with engine.begin() as conn:
        yield conn


__all__ = ["engine", "get_connection", "get_writable_connection", "metadata"]

