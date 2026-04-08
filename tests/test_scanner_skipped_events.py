from __future__ import annotations

from pathlib import Path

from ksbody.watcher.handler import is_recipe_body_filename
from ksbody.watcher.scanner import FileStateStore, FullScanner


class _DummyEventRepo:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, str | None]] = []

    def record_event(self, source_file: str, event_type: str, error_message: str | None = None) -> None:
        self.events.append((source_file, event_type, error_message))


def test_scanner_records_skipped_when_mtime_unchanged(tmp_path: Path) -> None:
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir(parents=True)
    source_file = watch_dir / "L_WBK_ConnX Elite@ECC17@BOP-A@WAF903898_1"
    source_file.write_bytes(b"same")

    state_store = FileStateStore(tmp_path / "state.json")
    mtime = source_file.stat().st_mtime
    state_store.mark_processed(source_file, mtime)
    state_store.save()

    callback_called = {"value": False}

    def callback(_: Path) -> bool:
        callback_called["value"] = True
        return True

    event_repo = _DummyEventRepo()
    scanner = FullScanner(
        watch_paths=[watch_dir],
        callback=callback,
        interval_seconds=1,
        state_store=state_store,
        file_filter=is_recipe_body_filename,
        event_repo=event_repo,
    )

    scanner.run_once()

    assert callback_called["value"] is False
    assert event_repo.events == [(str(source_file), "skipped", "unchanged_mtime")]
