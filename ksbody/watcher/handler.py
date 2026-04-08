from __future__ import annotations

from pathlib import Path
import logging
import re
import time
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler

from ksbody.config import DebounceConfig
from ksbody.watcher.scanner import FileStateStore


RECIPE_BODY_PATTERN = re.compile(r"^L_[^@]+@[^@]+@[^@]+@[^_]+_\d+$")



def is_recipe_body_filename(path: str | Path) -> bool:
    return bool(RECIPE_BODY_PATTERN.match(Path(path).name))


class RecipeBodyHandler(FileSystemEventHandler):
    def __init__(
        self,
        callback: Callable[[Path], bool],
        debounce: DebounceConfig,
        state_store: FileStateStore,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__()
        self.callback = callback
        self.debounce = debounce
        self.state_store = state_store
        self.logger = logger or logging.getLogger(__name__)

    def on_created(self, event: FileSystemEvent) -> None:
        self._handle_event(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._handle_event(event)

    def _handle_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        path = Path(event.src_path)
        if not is_recipe_body_filename(path):
            return

        if not self._wait_until_stable(path):
            self.logger.warning("debounce timeout: %s", path)
            return

        try:
            mtime = path.stat().st_mtime
        except OSError:
            return

        if mtime <= self.state_store.get_last_mtime(path):
            return

        if self.callback(path):
            self.state_store.mark_processed(path, mtime)
            self.state_store.save()

    def _wait_until_stable(self, path: Path) -> bool:
        stable_seen = 0
        previous_signature: tuple[int, int] | None = None
        deadline = time.time() + self.debounce.settle_seconds

        while time.time() < deadline:
            if not path.exists():
                return False
            try:
                stat = path.stat()
            except OSError:
                return False

            signature = (stat.st_mtime_ns, stat.st_size)
            if signature == previous_signature:
                stable_seen += 1
            else:
                stable_seen = 1
                previous_signature = signature

            if stable_seen >= self.debounce.stable_checks:
                return True

            time.sleep(self.debounce.poll_seconds)

        return False
