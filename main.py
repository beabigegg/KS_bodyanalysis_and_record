from __future__ import annotations

import argparse
from pathlib import Path
import logging
import time

from config.settings import load_settings
from db.repository import RecipeRepository
from db.schema import metadata
from pipeline import RecipePipeline
from watcher.handler import RecipeBodyHandler, is_recipe_body_filename
from watcher.observer import create_polling_observer
from watcher.scanner import FileStateStore, FullScanner



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

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root.handlers.clear()
    root.addHandler(stream_handler)
    root.addHandler(file_handler)



def build_callback(pipeline: RecipePipeline, logger: logging.Logger):
    def process_file(path: Path) -> bool:
        try:
            result = pipeline.process(path)
        except Exception:  # noqa: BLE001
            logger.exception("recipe_failed source_file=%s", path)
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
        return True

    return process_file



def main() -> None:
    parser = argparse.ArgumentParser(description="KS recipe body watcher and parser service")
    parser.add_argument(
        "--config",
        help="Deprecated and ignored. Pipeline settings are loaded from environment variables.",
    )
    parser.add_argument(
        "--process-file",
        help="Process one recipe body file and exit (for validation)",
    )
    args = parser.parse_args()

    settings = load_settings()
    configure_logging(settings.log_file)
    logger = logging.getLogger("recipe_service")

    repository = RecipeRepository.from_settings(settings)
    metadata.create_all(repository.engine)
    pipeline = RecipePipeline(repository=repository, logger=logger)

    callback = build_callback(pipeline, logger)

    if args.process_file:
        callback(Path(args.process_file))
        return

    state_store = FileStateStore(settings.state_file)
    handler = RecipeBodyHandler(callback, settings.debounce, state_store, logger=logger)
    observer = create_polling_observer(settings.watch_paths, handler, logger=logger)

    scanner = FullScanner(
        watch_paths=settings.watch_paths,
        callback=callback,
        interval_seconds=settings.scan_interval,
        state_store=state_store,
        file_filter=is_recipe_body_filename,
        last_import_lookup=lambda path: repository.get_last_import_epoch(str(path)),
        logger=logger,
    )

    observer.start()
    scanner.start()
    logger.info("watch service started")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("shutdown signal received")
    finally:
        scanner.stop()
        observer.stop()
        observer.join()
        logger.info("watch service stopped")


if __name__ == "__main__":
    main()
