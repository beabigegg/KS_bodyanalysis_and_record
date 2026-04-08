from __future__ import annotations

from pathlib import Path
import json
import logging
import threading
import time
from typing import Callable


class FileStateStore:
    """Track the last processed mtime for each file path."""

    def __init__(self, state_file: str | Path) -> None:
        self.state_file = Path(state_file)
        self._lock = threading.Lock()
        self._data: dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        if not self.state_file.exists():
            return
        try:
            self._data = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self._data = {}

    def save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self.state_file.write_text(
                json.dumps(self._data, ensure_ascii=True, indent=2),
                encoding="utf-8",
            )

    def get_last_mtime(self, file_path: str | Path) -> float:
        with self._lock:
            return float(self._data.get(str(Path(file_path)), 0.0))

    def mark_processed(self, file_path: str | Path, mtime: float) -> None:
        with self._lock:
            self._data[str(Path(file_path))] = float(mtime)


class FullScanner:
    def __init__(
        self,
        watch_paths: list[Path],
        callback: Callable[[Path], bool],
        interval_seconds: int,
        state_store: FileStateStore,
        file_filter: Callable[[Path], bool],
        last_import_lookup: Callable[[Path], float] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.watch_paths = watch_paths
        self.callback = callback
        self.interval_seconds = interval_seconds
        self.state_store = state_store
        self.file_filter = file_filter
        self.last_import_lookup = last_import_lookup
        self.logger = logger or logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=5)
        self.state_store.save()

    def run_once(self) -> None:
        updated = False
        for root in self.watch_paths:
            if not root.exists():
                continue

            for file_path in root.rglob("*"):
                if not file_path.is_file() or not self.file_filter(file_path):
                    continue

                try:
                    mtime = file_path.stat().st_mtime
                except OSError:
                    continue

                last_seen = self.state_store.get_last_mtime(file_path)
                if self.last_import_lookup is not None:
                    try:
                        last_seen = max(last_seen, self.last_import_lookup(file_path))
                    except Exception:  # noqa: BLE001
                        self.logger.exception("last import lookup failed: %s", file_path)

                if mtime <= last_seen:
                    continue

                if self.callback(file_path):
                    self.state_store.mark_processed(file_path, mtime)
                    updated = True

        if updated:
            self.state_store.save()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:  # noqa: BLE001
                self.logger.exception("full scanner run failed")
            time.sleep(self.interval_seconds)
