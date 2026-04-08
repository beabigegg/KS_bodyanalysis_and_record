from __future__ import annotations

import argparse

import uvicorn

from ksbody.config import get_settings
from ksbody.db.init_db import ensure_schema, init_db
from ksbody.manager import ProcessManager
from ksbody.pipeline.runner import run_pipeline


def _run_web() -> None:
    settings = get_settings()
    log_level = "debug" if settings.debug else "info"
    uvicorn.run(
        "ksbody.web.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.app_mode == "dev"),
        log_level=log_level,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="KS Body Analysis service launcher")
    subparsers = parser.add_subparsers(dest="command")

    pipeline_parser = subparsers.add_parser("pipeline", help="Run the folder watcher pipeline")
    pipeline_parser.add_argument(
        "--process-file",
        help="Process one recipe body file and exit (for validation)",
    )

    subparsers.add_parser("web", help="Run the FastAPI web service")
    subparsers.add_parser("all", help="Run pipeline and web together")
    subparsers.add_parser("init-db", help="Initialize database schema and exit")

    args = parser.parse_args()

    if args.command == "pipeline":
        ensure_schema()
        run_pipeline(process_file=args.process_file)
        return
    if args.command == "web":
        ensure_schema()
        _run_web()
        return
    if args.command == "all":
        ensure_schema()
        ProcessManager().run()
        return
    if args.command == "init-db":
        init_db()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
