from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Connection, create_engine, insert
from sqlalchemy.pool import StaticPool

from ksbody.db.schema import cleanup_log, metadata, watcher_events
from ksbody.timeutils import now_utc8
from ksbody.web.deps import get_connection, get_writable_connection
from ksbody.web.routes.watcher import router


class _DummyStateStore:
    def __init__(self) -> None:
        self.cleared: list[str] = []
        self.cleared_many: list[str] = []

    def clear(self, file_path: str) -> None:
        self.cleared.append(file_path)

    def clear_many(self, file_paths: list[str]) -> None:
        self.cleared_many.extend(file_paths)


def _recipe_name(index: int) -> str:
    return f"L_WBK_ConnX Elite@ECC17@BOP-A@WAF903898_{index}"


def _timestamp_recipe_name(index: int) -> str:
    return f"L_WBK_ConnX Elite@ECC17@BOP-A@WAF903898_{index}_1775539{index:03d}"


@pytest.fixture()
def app_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    watch_dir = tmp_path / "smb" / "recipes"
    watch_dir.mkdir(parents=True)

    test_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    metadata.create_all(test_engine)

    def _get_conn() -> Generator[Connection, None, None]:
        with test_engine.connect() as conn:
            yield conn

    def _get_writable_conn() -> Generator[Connection, None, None]:
        with test_engine.begin() as conn:
            yield conn

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_connection] = _get_conn
    app.dependency_overrides[get_writable_connection] = _get_writable_conn

    mock_settings = type("S", (), {"watch_paths": [watch_dir], "scan_interval": 300})()
    monkeypatch.setattr("ksbody.web.routes.watcher.settings", mock_settings)
    state_store = _DummyStateStore()
    monkeypatch.setattr("ksbody.web.routes._state_store.get_state_store", lambda: state_store)

    yield {"client": TestClient(app), "watch_dir": watch_dir, "engine": test_engine, "state_store": state_store}


def test_status_disk_usage_and_files_endpoints(app_state) -> None:
    client: TestClient = app_state["client"]
    watch_dir: Path = app_state["watch_dir"]
    engine = app_state["engine"]

    file_1 = watch_dir / _recipe_name(1)
    file_2 = watch_dir / _recipe_name(2)
    file_1.write_bytes(b"a")
    file_2.write_bytes(b"b")

    with engine.begin() as conn:
        conn.execute(
            insert(watcher_events).values(
                id=1,
                source_file=str(file_1),
                event_type="processed",
                event_datetime=now_utc8() - timedelta(hours=1),
            )
        )
        conn.execute(
            insert(watcher_events).values(
                id=2,
                source_file=str(file_2),
                event_type="failed",
                error_message="bad file",
                event_datetime=now_utc8(),
            )
        )

    status_response = client.get("/api/watcher/status")
    assert status_response.status_code == 200
    assert status_response.json()["running"] is True
    assert status_response.json()["watch_paths"][0]["file_count"] == 2

    disk_response = client.get("/api/watcher/disk-usage")
    assert disk_response.status_code == 200
    assert len(disk_response.json()["data"]) == 1

    files_response = client.get("/api/watcher/files", params={"page": 1, "page_size": 20})
    assert files_response.status_code == 200
    payload = files_response.json()
    assert payload["total"] == 2
    statuses = {row["path"]: row["status"] for row in payload["data"]}
    assert statuses[str(file_1)] == "processed"
    assert statuses[str(file_2)] == "failed"

    failed_response = client.get("/api/watcher/files", params={"status_filter": "failed"})
    assert failed_response.status_code == 200
    assert failed_response.json()["total"] == 1


def test_status_and_files_include_timestamp_suffix_recipe(app_state) -> None:
    client: TestClient = app_state["client"]
    watch_dir: Path = app_state["watch_dir"]
    engine = app_state["engine"]

    source_file = watch_dir / _timestamp_recipe_name(7)
    source_file.write_bytes(b"timestamp")

    with engine.begin() as conn:
        conn.execute(
            insert(watcher_events).values(
                id=1,
                source_file=str(source_file),
                event_type="processed",
                event_datetime=now_utc8(),
            )
        )

    status_response = client.get("/api/watcher/status")
    assert status_response.status_code == 200
    assert status_response.json()["watch_paths"][0]["file_count"] == 1

    files_response = client.get("/api/watcher/files")
    assert files_response.status_code == 200
    assert files_response.json()["total"] == 1
    assert files_response.json()["data"][0]["path"] == str(source_file)


def test_stats_events_reparse_cleanup_endpoints(app_state) -> None:
    client: TestClient = app_state["client"]
    watch_dir: Path = app_state["watch_dir"]
    state_store: _DummyStateStore = app_state["state_store"]
    engine = app_state["engine"]

    source_file = watch_dir / _recipe_name(5)
    source_file.write_bytes(b"abc")

    now = now_utc8()
    with engine.begin() as conn:
        conn.execute(
            insert(watcher_events).values(
                id=1,
                source_file=str(source_file),
                event_type="processed",
                event_datetime=now - timedelta(minutes=5),
            )
        )
        conn.execute(
            insert(watcher_events).values(
                id=2,
                source_file=str(source_file),
                event_type="failed",
                error_message="parse failed",
                event_datetime=now,
            )
        )
        conn.execute(
            insert(cleanup_log).values(
                id=1,
                source_file=str(source_file),
                file_size_bytes=123,
                file_mtime=now - timedelta(days=1),
                deleted_at=now,
                trigger="manual",
            )
        )

    stats_response = client.get("/api/watcher/stats")
    assert stats_response.status_code == 200
    assert stats_response.json()["today"]["total"] >= 2

    events_response = client.get("/api/watcher/events", params={"event_type": "failed"})
    assert events_response.status_code == 200
    assert events_response.json()["total"] == 1

    reparse_submit = client.post("/api/watcher/reparse", json={"source_files": [str(source_file)]})
    assert reparse_submit.status_code == 200
    task_ids = reparse_submit.json()["task_ids"]
    assert len(task_ids) == 1
    assert state_store.cleared_many == [str(source_file)]

    reparse_status = client.get("/api/watcher/reparse", params={"task_ids": ",".join(str(i) for i in task_ids)})
    assert reparse_status.status_code == 200
    assert reparse_status.json()["total"] == 1

    cleanup_config = client.get("/api/watcher/cleanup/config")
    assert cleanup_config.status_code == 200
    assert cleanup_config.json()["threshold_percent"] == 80

    cleanup_update = client.put("/api/watcher/cleanup/config", json={"enabled": True, "threshold_percent": 75})
    assert cleanup_update.status_code == 200
    assert cleanup_update.json() == {"enabled": True, "threshold_percent": 75}

    cleanup_log_response = client.get("/api/watcher/cleanup/log", params={"trigger_filter": "manual"})
    assert cleanup_log_response.status_code == 200
    assert cleanup_log_response.json()["total"] == 1
