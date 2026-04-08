from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine, insert, select
from sqlalchemy.pool import StaticPool

from ksbody.db.schema import metadata, reparse_tasks
from ksbody.pipeline.runner import _process_reparse_tasks
from ksbody.timeutils import now_utc8


def _make_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    metadata.create_all(engine)
    return engine


def test_process_reparse_tasks_executes_pending_file(tmp_path: Path) -> None:
    engine = _make_engine()
    source_file = tmp_path / "L_WBK_ConnX Elite@ECC17@BOP-A@WAF903898_1"
    source_file.write_bytes(b"reparse")

    with engine.begin() as conn:
        conn.execute(
            insert(reparse_tasks).values(
                id=1,
                source_file=str(source_file),
                status="pending",
                created_at=now_utc8(),
            )
        )

    called: list[Path] = []

    def callback(path: Path) -> bool:
        called.append(path)
        return True

    _process_reparse_tasks(engine, callback, logging.getLogger("test"))

    assert called == [source_file]
    with engine.connect() as conn:
        row = conn.execute(select(reparse_tasks).where(reparse_tasks.c.id == 1)).first()
    assert row is not None
    assert row.status == "completed"
    assert row.started_at is not None
    assert row.completed_at is not None
