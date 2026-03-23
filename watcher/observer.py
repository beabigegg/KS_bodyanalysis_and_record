from __future__ import annotations

from pathlib import Path
import logging

from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver


def create_polling_observer(
    watch_paths: list[Path],
    event_handler: FileSystemEventHandler,
    logger: logging.Logger | None = None,
) -> PollingObserver:
    log = logger or logging.getLogger(__name__)
    observer = PollingObserver()

    scheduled = 0
    for path in watch_paths:
        if not path.exists():
            log.warning("watch path unavailable: %s", path)
            continue
        observer.schedule(event_handler, str(path), recursive=True)
        scheduled += 1
        log.info("watch path enabled: %s", path)

    if scheduled == 0:
        raise RuntimeError("No valid watch paths available.")

    return observer
