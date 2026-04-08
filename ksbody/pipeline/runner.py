from __future__ import annotations

from pathlib import Path
import logging
import shutil
import threading
import time
from typing import Callable

from sqlalchemy import Engine, Table, func, insert, select, update

from ksbody.config import get_settings
from ksbody.db.init_db import ensure_schema
from ksbody.db.repository import RecipeRepository, WatcherEventRepository
from ksbody.db.schema import cleanup_config, cleanup_log, reparse_tasks
from ksbody.pipeline import RecipePipeline
from ksbody.timeutils import from_timestamp_utc8, now_utc8
from ksbody.watcher.handler import RecipeBodyHandler, is_recipe_body_filename
from ksbody.watcher.observer import create_polling_observer
from ksbody.watcher.scanner import FileStateStore, FullScanner

CLEANUP_CHECK_INTERVAL_SECONDS = 3600


def _insert_with_pk_compat(conn, table: Table, values: dict) -> None:
    payload = dict(values)
    if conn.dialect.name == "sqlite" and "id" in table.c and "id" not in payload:
        max_id = conn.execute(select(func.max(table.c.id))).scalar_one_or_none() or 0
        payload["id"] = int(max_id) + 1
    conn.execute(insert(table).values(**payload))


def configure_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)

    root.handlers.clear()
    root.addHandler(stream_handler)
    root.addHandler(file_handler)


def build_callback(
    pipeline: RecipePipeline,
    logger: logging.Logger,
    event_repo: WatcherEventRepository | None = None,
):
    def process_file(path: Path) -> bool:
        try:
            result = pipeline.process(path)
        except Exception:  # noqa: BLE001
            logger.exception("recipe_failed source_file=%s", path)
            if event_repo:
                try:
                    import traceback
                    event_repo.record_event(str(path), "failed", traceback.format_exc())
                except Exception:  # noqa: BLE001
                    logger.exception("failed to record event for %s", path)
            return False

        logger.info(
            "recipe_processed source_file=%s import_id=%s parsed=%s failed=%s skipped=%s params=%s bsg=%s rpm_limits=%s rpm_ref=%s",
            result.source_file,
            result.recipe_import_id,
            result.parsed_files,
            result.failed_files,
            result.skipped_files,
            result.parameter_count,
            result.bsg_count,
            result.rpm_limits_count,
            result.rpm_reference_count,
        )
        if event_repo:
            try:
                event_repo.record_event(str(path), "processed")
            except Exception:  # noqa: BLE001
                logger.exception("failed to record event for %s", path)
        return True

    return process_file


def _process_reparse_tasks(
    engine: Engine,
    callback: Callable[[Path], bool],
    logger: logging.Logger,
) -> None:
    """Check DB for pending reparse tasks and execute them."""
    with engine.begin() as conn:
        # Reset any stuck 'running' tasks to 'pending' (from prior crash)
        conn.execute(
            update(reparse_tasks)
            .where(reparse_tasks.c.status == "running")
            .values(status="pending", started_at=None)
        )

    with engine.connect() as conn:
        pending = conn.execute(
            select(reparse_tasks)
            .where(reparse_tasks.c.status == "pending")
            .order_by(reparse_tasks.c.created_at.asc())
        ).all()

    for task in pending:
        task_id = task.id
        source_file = task.source_file
        logger.info("reparse_start task_id=%s source_file=%s", task_id, source_file)

        with engine.begin() as conn:
            conn.execute(
                update(reparse_tasks)
                .where(reparse_tasks.c.id == task_id)
                .values(status="running", started_at=now_utc8())
            )

        path = Path(source_file)
        if not path.exists():
            with engine.begin() as conn:
                conn.execute(
                    update(reparse_tasks)
                    .where(reparse_tasks.c.id == task_id)
                    .values(
                        status="failed",
                        error_message="File not found",
                        completed_at=now_utc8(),
                    )
                )
            continue

        success = callback(path)
        with engine.begin() as conn:
            conn.execute(
                update(reparse_tasks)
                .where(reparse_tasks.c.id == task_id)
                .values(
                    status="completed" if success else "failed",
                    error_message=None if success else "Pipeline processing failed",
                    completed_at=now_utc8(),
                )
            )
        logger.info("reparse_done task_id=%s success=%s", task_id, success)


def _ensure_cleanup_config_row(engine: Engine) -> None:
    with engine.begin() as conn:
        row = conn.execute(select(cleanup_config.c.id).limit(1)).first()
        if row is None:
            now = now_utc8()
            _insert_with_pk_compat(
                conn,
                cleanup_config,
                {
                    "enabled": False,
                    "threshold_percent": 80,
                    "last_run_at": None,
                    "updated_at": now,
                },
            )


def _get_cleanup_usage_percent(watch_paths: list[Path], logger: logging.Logger) -> float | None:
    usage_values: list[float] = []
    for wp in watch_paths:
        try:
            usage = shutil.disk_usage(wp.resolve())
        except OSError:
            logger.debug("cleanup_skip_unavailable_watch_path path=%s", wp)
            continue
        if usage.total > 0:
            usage_values.append((usage.used / usage.total) * 100.0)
    if not usage_values:
        return None
    return max(usage_values)


def _list_recipe_body_files(watch_paths: list[Path], logger: logging.Logger) -> list[Path]:
    files: list[Path] = []
    for root in watch_paths:
        root_path = root.resolve()
        if not root_path.exists():
            continue
        try:
            for file_path in root_path.rglob("*"):
                if file_path.is_file() and is_recipe_body_filename(file_path):
                    files.append(file_path)
        except OSError:
            logger.debug("cleanup_scan_failed path=%s", root_path)
    files.sort(key=lambda p: p.stat().st_mtime if p.exists() else float("inf"))
    return files


def _run_auto_cleanup_once(engine: Engine, watch_paths: list[Path], logger: logging.Logger) -> None:
    _ensure_cleanup_config_row(engine)

    with engine.begin() as conn:
        cfg = conn.execute(select(cleanup_config).limit(1)).first()
        if cfg is None:
            return
        conn.execute(
            update(cleanup_config)
            .where(cleanup_config.c.id == cfg.id)
            .values(last_run_at=now_utc8())
        )

    if not bool(cfg.enabled):
        logger.debug("cleanup_skipped reason=disabled")
        return

    usage_before = _get_cleanup_usage_percent(watch_paths, logger)
    if usage_before is None:
        logger.debug("cleanup_skipped reason=no_accessible_watch_paths")
        return
    if usage_before <= float(cfg.threshold_percent):
        logger.debug(
            "cleanup_skipped reason=under_threshold usage=%.2f threshold=%s",
            usage_before,
            cfg.threshold_percent,
        )
        return

    deleted_count = 0
    released_bytes = 0
    now = now_utc8()
    for file_path in _list_recipe_body_files(watch_paths, logger):
        current_usage = _get_cleanup_usage_percent(watch_paths, logger)
        if current_usage is None or current_usage <= float(cfg.threshold_percent):
            break

        try:
            stat = file_path.stat()
        except FileNotFoundError:
            logger.debug("cleanup_skip_missing path=%s", file_path)
            continue
        except OSError:
            logger.debug("cleanup_skip_unreadable path=%s", file_path)
            continue

        try:
            file_path.unlink()
        except FileNotFoundError:
            logger.debug("cleanup_skip_missing path=%s", file_path)
            continue
        except OSError:
            logger.exception("cleanup_delete_failed path=%s", file_path)
            continue

        deleted_count += 1
        released_bytes += int(stat.st_size)
        with engine.begin() as conn:
            _insert_with_pk_compat(
                conn,
                cleanup_log,
                {
                    "source_file": str(file_path),
                    "file_size_bytes": int(stat.st_size),
                    "file_mtime": from_timestamp_utc8(stat.st_mtime),
                    "deleted_at": now,
                    "trigger": "auto",
                },
            )

    usage_after = _get_cleanup_usage_percent(watch_paths, logger)
    logger.info(
        "cleanup_run usage_before=%.2f usage_after=%s deleted_files=%s released_bytes=%s",
        usage_before,
        f"{usage_after:.2f}" if usage_after is not None else "n/a",
        deleted_count,
        released_bytes,
    )


def run_pipeline(process_file: str | None = None) -> None:
    settings = get_settings()
    configure_logging(settings.log_file)
    logger = logging.getLogger("recipe_service")
    ensure_schema()

    if process_file:
        # Validation mode: process one file and exit without requiring DB connectivity.
        pipeline = RecipePipeline(repository=None, logger=logger)
        callback = build_callback(pipeline, logger)
        callback(Path(process_file))
        return

    repository = RecipeRepository.from_settings(settings)
    ensure_schema(repository.engine)
    event_repo = WatcherEventRepository(repository.engine)
    pipeline = RecipePipeline(repository=repository, logger=logger)
    callback = build_callback(pipeline, logger, event_repo=event_repo)
    _ensure_cleanup_config_row(repository.engine)

    state_store = FileStateStore(settings.state_file)
    handler = RecipeBodyHandler(callback, settings.debounce, state_store, logger=logger, event_repo=event_repo)
    observer = create_polling_observer(settings.watch_paths, handler, logger=logger)

    scanner = FullScanner(
        watch_paths=settings.watch_paths,
        callback=callback,
        interval_seconds=settings.scan_interval,
        state_store=state_store,
        file_filter=is_recipe_body_filename,
        last_import_lookup=lambda path: repository.get_last_import_epoch(str(path)),
        logger=logger,
        event_repo=event_repo,
    )

    # Reset any stuck reparse tasks from prior crash (task 6.4)
    _process_reparse_tasks(repository.engine, callback, logger)

    # Reparse checker thread
    reparse_stop = threading.Event()
    cleanup_stop = threading.Event()

    def _reparse_loop():
        while not reparse_stop.is_set():
            try:
                _process_reparse_tasks(repository.engine, callback, logger)
            except Exception:  # noqa: BLE001
                logger.exception("reparse check failed")
            reparse_stop.wait(timeout=settings.scan_interval)

    reparse_thread = threading.Thread(target=_reparse_loop, daemon=True)

    def _cleanup_loop():
        while not cleanup_stop.is_set():
            try:
                _run_auto_cleanup_once(repository.engine, settings.watch_paths, logger)
            except Exception:  # noqa: BLE001
                logger.exception("cleanup check failed")
            cleanup_stop.wait(timeout=CLEANUP_CHECK_INTERVAL_SECONDS)

    cleanup_thread = threading.Thread(target=_cleanup_loop, daemon=True)

    observer.start()
    scanner.start()
    reparse_thread.start()
    cleanup_thread.start()
    logger.info("watch service started")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("shutdown signal received")
    finally:
        reparse_stop.set()
        cleanup_stop.set()
        scanner.stop()
        observer.stop()
        observer.join()
        logger.info("watch service stopped")
