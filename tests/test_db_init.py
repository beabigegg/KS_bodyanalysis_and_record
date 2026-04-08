from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from ksbody.db.init_db import ensure_schema


def _make_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def test_ensure_schema_creates_all_tables() -> None:
    engine = _make_engine()

    ensure_schema(engine)

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    assert "ksbody_recipe_import" in table_names
    assert "ksbody_recipe_params" in table_names
    assert "ksbody_watcher_events" in table_names
    assert "ksbody_cleanup_log" in table_names


def test_ensure_schema_is_idempotent() -> None:
    engine = _make_engine()
    ensure_schema(engine)

    with engine.begin() as conn:
        conn.execute(
            text(
                "insert into ksbody_cleanup_config "
                "(id, enabled, threshold_percent, last_run_at, updated_at) "
                "values (1, 0, 80, null, '2026-04-08 00:00:00')"
            )
        )

    ensure_schema(engine)

    with engine.connect() as conn:
        count = conn.execute(text("select count(*) from ksbody_cleanup_config")).scalar_one()
    assert count == 1
