from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os

from sqlalchemy import create_engine, insert, select
from sqlalchemy.pool import StaticPool

from ksbody.db.schema import cleanup_config, cleanup_log, metadata
from ksbody.pipeline.runner import _run_auto_cleanup_once


class _DummyLogger:
    def debug(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None

    def info(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None

    def exception(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None


def _make_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    metadata.create_all(engine)
    return engine


def _recipe_name(index: int) -> str:
    return f"L_WBK_ConnX Elite@ECC17@BOP-A@WAF903898_{index}"


def test_cleanup_initializes_default_config(tmp_path: Path) -> None:
    engine = _make_engine()
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir(parents=True)

    _run_auto_cleanup_once(engine, [watch_dir], _DummyLogger())

    with engine.connect() as conn:
        row = conn.execute(select(cleanup_config)).first()
    assert row is not None
    assert row.enabled is False
    assert row.threshold_percent == 80


def test_cleanup_deletes_oldest_files_and_records_logs(tmp_path: Path) -> None:
    engine = _make_engine()
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir(parents=True)
    old_file = watch_dir / _recipe_name(1)
    new_file = watch_dir / _recipe_name(2)
    old_file.write_bytes(b"old")
    new_file.write_bytes(b"new")
    # Ensure old_file has smaller mtime.
    old_file_epoch = old_file.stat().st_mtime - 10
    os.utime(old_file, (old_file_epoch, old_file_epoch))

    with engine.begin() as conn:
        conn.execute(
            insert(cleanup_config).values(
                id=1,
                enabled=True,
                threshold_percent=-1,
                updated_at=datetime(2026, 1, 1, 0, 0, 0),
            )
        )

    _run_auto_cleanup_once(engine, [watch_dir], _DummyLogger())

    assert not old_file.exists()
    assert not new_file.exists()

    with engine.connect() as conn:
        rows = conn.execute(select(cleanup_log).order_by(cleanup_log.c.id.asc())).all()
    assert len(rows) == 2
    assert rows[0].trigger == "auto"
    assert rows[1].trigger == "auto"


def test_cleanup_disabled_is_noop(tmp_path: Path) -> None:
    engine = _make_engine()
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir(parents=True)
    file_path = watch_dir / _recipe_name(3)
    file_path.write_bytes(b"keep")

    with engine.begin() as conn:
        conn.execute(
            insert(cleanup_config).values(
                id=1,
                enabled=False,
                threshold_percent=-1,
                updated_at=datetime(2026, 1, 1, 0, 0, 0),
            )
        )

    _run_auto_cleanup_once(engine, [watch_dir], _DummyLogger())

    assert file_path.exists()
    with engine.connect() as conn:
        logs = conn.execute(select(cleanup_log)).all()
        cfg = conn.execute(select(cleanup_config).where(cleanup_config.c.id == 1)).first()
    assert logs == []
    assert cfg is not None
    assert cfg.last_run_at is not None


def test_cleanup_under_threshold_is_noop(tmp_path: Path) -> None:
    engine = _make_engine()
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir(parents=True)
    file_path = watch_dir / _recipe_name(4)
    file_path.write_bytes(b"keep")

    with engine.begin() as conn:
        conn.execute(
            insert(cleanup_config).values(
                id=1,
                enabled=True,
                threshold_percent=100,
                updated_at=datetime(2026, 1, 1, 0, 0, 0),
            )
        )

    _run_auto_cleanup_once(engine, [watch_dir], _DummyLogger())

    assert file_path.exists()
    with engine.connect() as conn:
        logs = conn.execute(select(cleanup_log)).all()
    assert logs == []
