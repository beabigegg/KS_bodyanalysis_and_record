from __future__ import annotations

from pathlib import Path

from ksbody.watcher.scanner import FileStateStore


def test_clear_removes_entry(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    store = FileStateStore(state_file)
    store.mark_processed("/smb/file1", 100.0)
    store.mark_processed("/smb/file2", 200.0)
    store.save()

    store.clear("/smb/file1")

    assert store.get_last_mtime("/smb/file1") == 0.0
    assert store.get_last_mtime("/smb/file2") == 200.0

    # Verify persisted
    reloaded = FileStateStore(state_file)
    assert reloaded.get_last_mtime("/smb/file1") == 0.0
    assert reloaded.get_last_mtime("/smb/file2") == 200.0


def test_clear_nonexistent_path_is_noop(tmp_path: Path) -> None:
    store = FileStateStore(tmp_path / "state.json")
    store.clear("/does/not/exist")  # should not raise


def test_clear_many_removes_multiple(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    store = FileStateStore(state_file)
    store.mark_processed("/smb/a", 1.0)
    store.mark_processed("/smb/b", 2.0)
    store.mark_processed("/smb/c", 3.0)
    store.save()

    store.clear_many(["/smb/a", "/smb/c"])

    assert store.get_last_mtime("/smb/a") == 0.0
    assert store.get_last_mtime("/smb/b") == 2.0
    assert store.get_last_mtime("/smb/c") == 0.0

    reloaded = FileStateStore(state_file)
    assert reloaded.get_last_mtime("/smb/a") == 0.0
    assert reloaded.get_last_mtime("/smb/b") == 2.0


def test_clear_many_empty_list_is_noop(tmp_path: Path) -> None:
    store = FileStateStore(tmp_path / "state.json")
    store.mark_processed("/smb/x", 5.0)
    store.save()
    store.clear_many([])
    assert store.get_last_mtime("/smb/x") == 5.0
