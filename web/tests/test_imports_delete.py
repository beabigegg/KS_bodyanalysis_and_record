"""
Tests for DELETE /api/imports/{import_id} and DELETE /api/imports/batch endpoints.

Uses an in-memory SQLite database so no real DB connection is needed.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WEB = Path(__file__).resolve().parents[1]
if str(WEB) not in sys.path:
    sys.path.insert(0, str(WEB))

from db.schema import metadata, recipe_import, recipe_params  # noqa: E402
import deps  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    """Create a TestClient backed by an in-memory SQLite DB."""
    test_engine = create_engine("sqlite:///:memory:", future=True)
    metadata.create_all(test_engine)

    def _get_conn():
        with test_engine.connect() as conn:
            yield conn

    def _get_writable_conn():
        with test_engine.begin() as conn:
            yield conn

    monkeypatch.setattr(deps, "engine", test_engine)

    # Import app after patching so routers pick up the patched deps
    from app import app  # noqa: PLC0415
    import routes.imports as imports_module  # noqa: PLC0415

    monkeypatch.setattr(imports_module, "get_connection", _get_conn, raising=False)
    monkeypatch.setattr(imports_module, "get_writable_connection", _get_writable_conn, raising=False)

    app.dependency_overrides[deps.get_connection] = _get_conn
    app.dependency_overrides[deps.get_writable_connection] = _get_writable_conn

    yield TestClient(app)

    app.dependency_overrides.clear()


def _insert_import(client_fixture) -> int:
    """Insert a minimal recipe_import row and return its id."""
    # We reach into the engine via the override
    from app import app  # noqa: PLC0415

    override = app.dependency_overrides.get(deps.get_writable_connection)
    assert override is not None
    gen = override()
    conn = next(gen)
    result = conn.execute(
        insert(recipe_import).values(
            machine_type="TEST",
            machine_id="M1",
            product_type="PT",
            bop="B",
            wafer_pn="W",
            recipe_version=1,
            source_file="test.txt",
            import_datetime=datetime(2024, 1, 1),
        )
    )
    import_id = result.inserted_primary_key[0]
    conn.execute(
        insert(recipe_params).values(
            recipe_import_id=import_id,
            file_type="EYE",
            param_name="TEST/param",
            param_value="1.0",
        )
    )
    try:
        next(gen)
    except StopIteration:
        pass
    return import_id


# ---------------------------------------------------------------------------
# Single delete
# ---------------------------------------------------------------------------


class TestSingleDelete:
    def test_delete_success(self, client):
        import_id = _insert_import(client)
        response = client.delete(f"/api/imports/{import_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["deleted"] == 1

        # Verify the record is gone
        check = client.get(f"/api/imports/{import_id}/summary")
        assert check.status_code == 404

    def test_delete_not_found(self, client):
        response = client.delete("/api/imports/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Batch delete
# ---------------------------------------------------------------------------


class TestBatchDelete:
    def test_batch_delete_success(self, client):
        id1 = _insert_import(client)
        id2 = _insert_import(client)
        response = client.delete("/api/imports/batch", json={"ids": [id1, id2]})
        assert response.status_code == 200
        assert response.json()["data"]["deleted"] == 2

        assert client.get(f"/api/imports/{id1}/summary").status_code == 404
        assert client.get(f"/api/imports/{id2}/summary").status_code == 404

    def test_batch_delete_empty_ids_returns_400(self, client):
        response = client.delete("/api/imports/batch", json={"ids": []})
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_batch_delete_partial_invalid_ids(self, client):
        """Batch delete with some non-existent IDs succeeds, returns actual deleted count."""
        import_id = _insert_import(client)
        response = client.delete("/api/imports/batch", json={"ids": [import_id, 999999]})
        assert response.status_code == 200
        # Only the real record gets deleted
        assert response.json()["data"]["deleted"] == 1
