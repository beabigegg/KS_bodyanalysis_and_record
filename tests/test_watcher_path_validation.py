from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from ksbody.web.routes.watcher import _validate_path_within_watch_paths


@pytest.fixture(autouse=True)
def _mock_watch_paths(tmp_path: Path):
    watch_dir = tmp_path / "smb" / "recipes"
    watch_dir.mkdir(parents=True)
    mock_settings = type("S", (), {"watch_paths": [watch_dir]})()
    with patch("ksbody.web.routes.watcher.settings", mock_settings):
        yield watch_dir


def test_valid_path_within_watch_dir(_mock_watch_paths: Path) -> None:
    target = _mock_watch_paths / "machine1" / "file1"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch()
    result = _validate_path_within_watch_paths(str(target))
    assert result == target.resolve()


def test_path_traversal_rejected(_mock_watch_paths: Path) -> None:
    evil = str(_mock_watch_paths / ".." / ".." / "etc" / "passwd")
    with pytest.raises(HTTPException) as exc_info:
        _validate_path_within_watch_paths(evil)
    assert exc_info.value.status_code == 400


def test_completely_outside_path_rejected(_mock_watch_paths: Path) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _validate_path_within_watch_paths("/tmp/evil_file")
    assert exc_info.value.status_code == 400


def test_relative_path_outside_rejected(_mock_watch_paths: Path) -> None:
    evil = str(_mock_watch_paths) + "/../../../etc/shadow"
    with pytest.raises(HTTPException) as exc_info:
        _validate_path_within_watch_paths(evil)
    assert exc_info.value.status_code == 400
