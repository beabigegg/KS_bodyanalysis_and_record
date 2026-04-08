from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Connection, create_engine, select
from sqlalchemy.pool import StaticPool

from ksbody.db.schema import cleanup_log, metadata
from ksbody.web.deps import get_connection, get_writable_connection
from ksbody.web.routes.watcher import router


class _DummyStateStore:
    def __init__(self) -> None:
        self.cleared: list[str] = []

    def clear(self, file_path: str) -> None:
        self.cleared.append(file_path)


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


def _recipe_name(index: int) -> str:
    return f"L_WBK_ConnX Elite@ECC17@BOP-A@WAF903898_{index}"


def test_delete_file_success_records_cleanup_log(app_state) -> None:
    client: TestClient = app_state["client"]
    watch_dir: Path = app_state["watch_dir"]
    state_store: _DummyStateStore = app_state["state_store"]
    engine = app_state["engine"]

    file_path = watch_dir / _recipe_name(1)
    file_path.write_bytes(b"abc123")
    mtime_epoch = file_path.stat().st_mtime

    response = client.request("DELETE", "/api/watcher/files", json={"source_files": [str(file_path)]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["results"] == [{"source_file": str(file_path), "deleted": True}]
    assert not file_path.exists()
    assert state_store.cleared == [str(file_path)]

    with engine.connect() as conn:
        rows = conn.execute(select(cleanup_log)).all()
    assert len(rows) == 1
    assert rows[0].source_file == str(file_path)
    assert rows[0].file_size_bytes == 6
    assert abs(rows[0].file_mtime.timestamp() - mtime_epoch) < 1e-6
    assert rows[0].trigger == "manual"


def test_delete_file_rejects_outside_path(app_state, tmp_path: Path) -> None:
    client: TestClient = app_state["client"]
    outside = tmp_path / "outside_file"
    outside.write_text("x", encoding="utf-8")

    response = client.request("DELETE", "/api/watcher/files", json={"source_files": [str(outside)]})
    assert response.status_code == 200
    assert response.json()["results"] == [
        {"source_file": str(outside), "deleted": False, "error": "Invalid path"}
    ]
    assert outside.exists()


def test_delete_file_missing_returns_error(app_state) -> None:
    client: TestClient = app_state["client"]
    watch_dir: Path = app_state["watch_dir"]
    missing = watch_dir / _recipe_name(99)

    response = client.request("DELETE", "/api/watcher/files", json={"source_files": [str(missing)]})
    assert response.status_code == 200
    assert response.json()["results"] == [
        {"source_file": str(missing), "deleted": False, "error": "File not found"}
    ]
