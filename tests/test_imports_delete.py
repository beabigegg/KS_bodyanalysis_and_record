from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert
from sqlalchemy.pool import StaticPool

from ksbody.db.schema import metadata, recipe_import, recipe_params
from ksbody.web.deps import get_connection, get_writable_connection
from ksbody.web.routes.imports import router


class _DummyStateStore:
    def __init__(self) -> None:
        self.cleared: list[str] = []
        self.cleared_many: list[str] = []

    def clear(self, file_path: str) -> None:
        self.cleared.append(file_path)

    def clear_many(self, file_paths: list[str]) -> None:
        self.cleared_many.extend(file_paths)


@pytest.fixture()
def app_state():
    test_engine = create_engine("sqlite+pysqlite:///:memory:", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    metadata.create_all(test_engine)

    def _get_conn():
        with test_engine.connect() as conn:
            yield conn

    def _get_writable_conn():
        with test_engine.begin() as conn:
            yield conn

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_connection] = _get_conn
    app.dependency_overrides[get_writable_connection] = _get_writable_conn
    yield {"client": TestClient(app), "engine": test_engine}


@pytest.fixture()
def client(app_state):
    return app_state["client"]


def _insert_import(app_state, import_id: int) -> int:
    with app_state["engine"].begin() as conn:
        conn.execute(insert(recipe_import).values(id=import_id, machine_type="TEST", machine_id=f"M{import_id}", product_type="PT", bop="B", wafer_pn="W", recipe_version=1, source_file="test.txt", import_datetime=datetime(2024, 1, 1)))
        conn.execute(insert(recipe_params).values(id=import_id, recipe_import_id=import_id, file_type="EYE", param_name="TEST/param", param_value="1.0"))
    return import_id


class TestSingleDelete:
    def test_delete_success(self, client, app_state):
        import_id = _insert_import(app_state, 1)
        response = client.delete(f"/api/imports/{import_id}")
        assert response.status_code == 200
        assert response.json()["data"]["deleted"] == 1
        assert client.get(f"/api/imports/{import_id}/summary").status_code == 404

    def test_delete_not_found(self, client):
        response = client.delete("/api/imports/999999")
        assert response.status_code == 404

    def test_delete_with_clear_state_true(self, client, app_state, monkeypatch):
        import_id = _insert_import(app_state, 3)
        store = _DummyStateStore()
        monkeypatch.setattr("ksbody.web.routes._state_store.get_state_store", lambda: store)

        response = client.delete(f"/api/imports/{import_id}", params={"clear_state": "true"})

        assert response.status_code == 200
        assert store.cleared == ["test.txt"]

    def test_delete_with_clear_state_false(self, client, app_state, monkeypatch):
        import_id = _insert_import(app_state, 4)
        store = _DummyStateStore()
        monkeypatch.setattr("ksbody.web.routes._state_store.get_state_store", lambda: store)

        response = client.delete(f"/api/imports/{import_id}", params={"clear_state": "false"})

        assert response.status_code == 200
        assert store.cleared == []


class TestBatchDelete:
    def test_batch_delete_success(self, client, app_state):
        id1 = _insert_import(app_state, 1)
        id2 = _insert_import(app_state, 2)
        response = client.request("DELETE", "/api/imports/batch", json={"ids": [id1, id2]})
        assert response.status_code == 200
        assert response.json()["data"]["deleted"] == 2

    def test_batch_delete_empty_ids_returns_400(self, client):
        response = client.request("DELETE", "/api/imports/batch", json={"ids": []})
        assert response.status_code == 400

    def test_batch_delete_partial_invalid_ids(self, client, app_state):
        import_id = _insert_import(app_state, 1)
        response = client.request("DELETE", "/api/imports/batch", json={"ids": [import_id, 999999]})
        assert response.status_code == 200
        assert response.json()["data"]["deleted"] == 1

    def test_batch_delete_with_clear_state_true(self, client, app_state, monkeypatch):
        id1 = _insert_import(app_state, 5)
        id2 = _insert_import(app_state, 6)
        store = _DummyStateStore()
        monkeypatch.setattr("ksbody.web.routes._state_store.get_state_store", lambda: store)

        response = client.request(
            "DELETE",
            "/api/imports/batch",
            json={"ids": [id1, id2], "clear_state": True},
        )

        assert response.status_code == 200
        assert response.json()["data"]["deleted"] == 2
        assert sorted(store.cleared_many) == ["test.txt", "test.txt"]

    def test_batch_delete_with_clear_state_false(self, client, app_state, monkeypatch):
        id1 = _insert_import(app_state, 7)
        store = _DummyStateStore()
        monkeypatch.setattr("ksbody.web.routes._state_store.get_state_store", lambda: store)

        response = client.request(
            "DELETE",
            "/api/imports/batch",
            json={"ids": [id1], "clear_state": False},
        )

        assert response.status_code == 200
        assert store.cleared_many == []
