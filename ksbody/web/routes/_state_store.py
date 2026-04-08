from __future__ import annotations

from ksbody.watcher.scanner import FileStateStore
from ksbody.config import get_settings

_store: FileStateStore | None = None


def get_state_store() -> FileStateStore | None:
    global _store
    if _store is None:
        try:
            settings = get_settings()
            _store = FileStateStore(settings.state_file)
        except Exception:  # noqa: BLE001
            return None
    return _store
