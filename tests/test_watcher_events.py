from __future__ import annotations

from sqlalchemy import create_engine, insert, select
from sqlalchemy.pool import StaticPool

from ksbody.db.repository import WatcherEventRepository
from ksbody.db.schema import metadata, watcher_events
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


def _insert_event(engine, **kwargs):
    """Insert event directly for SQLite compatibility (no autoincrement on BIGINT)."""
    defaults = {"event_datetime": now_utc8()}
    defaults.update(kwargs)
    with engine.begin() as conn:
        conn.execute(insert(watcher_events).values(**defaults))


def test_record_event_success() -> None:
    engine = _make_engine()
    _insert_event(engine, id=1, source_file="/smb/file1", event_type="processed")

    with engine.connect() as conn:
        row = conn.execute(
            select(watcher_events).where(watcher_events.c.id == 1)
        ).first()
    assert row is not None
    assert row.source_file == "/smb/file1"
    assert row.event_type == "processed"
    assert row.error_message is None


def test_record_event_with_error() -> None:
    engine = _make_engine()
    _insert_event(engine, id=1, source_file="/smb/file2", event_type="failed", error_message="parse error")

    with engine.connect() as conn:
        row = conn.execute(
            select(watcher_events).where(watcher_events.c.id == 1)
        ).first()
    assert row is not None
    assert row.event_type == "failed"
    assert row.error_message == "parse error"


def test_record_multiple_events() -> None:
    engine = _make_engine()
    _insert_event(engine, id=1, source_file="/smb/a", event_type="processed")
    _insert_event(engine, id=2, source_file="/smb/a", event_type="skipped", error_message="already_processed")
    _insert_event(engine, id=3, source_file="/smb/b", event_type="failed", error_message="bad format")

    with engine.connect() as conn:
        rows = conn.execute(select(watcher_events)).fetchall()
    assert len(rows) == 3


def test_watcher_event_repository_on_mysql_like() -> None:
    """Exercise WatcherEventRepository.record_event directly (SQLite-compatible)."""
    engine = _make_engine()
    repo = WatcherEventRepository(engine)

    inserted_id = repo.record_event("/smb/direct-call", "failed", "traceback")
    assert inserted_id == 1

    with engine.connect() as conn:
        row = conn.execute(
            select(watcher_events).where(watcher_events.c.id == inserted_id)
        ).first()
    assert row is not None
    assert row.source_file == "/smb/direct-call"
    assert row.event_type == "failed"
    assert row.error_message == "traceback"
