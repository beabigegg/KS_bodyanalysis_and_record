from __future__ import annotations

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import Connection, Table, and_, func, insert, select, update

from ksbody.config import get_settings
from ksbody.db.schema import (
    cleanup_config,
    cleanup_log,
    reparse_tasks,
    watcher_events,
)
from ksbody.watcher.handler import is_recipe_body_filename
from ksbody.web.deps import get_connection, get_writable_connection
from ksbody.timeutils import from_timestamp_utc8, now_utc8

router = APIRouter(prefix="/api/watcher", tags=["watcher"])

settings = get_settings()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_path_within_watch_paths(file_path: str) -> Path:
    """Ensure the given path resolves under one of the configured watch paths."""
    resolved = Path(file_path).resolve()
    for wp in settings.watch_paths:
        if resolved.is_relative_to(wp.resolve()):
            return resolved
    raise HTTPException(status_code=400, detail="Path is not within any configured watch path")


def _disk_usage_for_watch_paths() -> list[dict[str, Any]]:
    seen_mounts: dict[str, dict[str, Any]] = {}
    for wp in settings.watch_paths:
        rp = str(wp.resolve())
        if rp in seen_mounts:
            continue
        try:
            usage = shutil.disk_usage(rp)
            seen_mounts[rp] = {
                "path": rp,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "usage_percent": round(usage.used / usage.total * 100, 1) if usage.total else 0,
            }
        except OSError:
            seen_mounts[rp] = {"path": rp, "total": 0, "used": 0, "free": 0, "usage_percent": 0}
    return list(seen_mounts.values())


def _insert_with_pk_compat(conn: Connection, table: Table, values: dict[str, Any]) -> None:
    payload = dict(values)
    if conn.dialect.name == "sqlite" and "id" in table.c and "id" not in payload:
        max_id = conn.execute(select(func.max(table.c.id))).scalar_one_or_none() or 0
        payload["id"] = int(max_id) + 1
    conn.execute(insert(table).values(**payload))


def _get_state_store_dep():
    from ksbody.web.routes._state_store import get_state_store

    return get_state_store()


def _ensure_cleanup_config_row(conn: Connection) -> Any:
    row = conn.execute(select(cleanup_config)).first()
    if row is not None:
        return row

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
    return conn.execute(select(cleanup_config)).first()


# ---------------------------------------------------------------------------
# 4.2 GET /api/watcher/status
# ---------------------------------------------------------------------------

@router.get("/status")
def watcher_status() -> dict[str, Any]:
    paths_info = []
    for wp in settings.watch_paths:
        rp = wp.resolve()
        exists = rp.exists()
        file_count = 0
        if exists:
            try:
                file_count = sum(1 for f in rp.rglob("*") if f.is_file() and is_recipe_body_filename(f))
            except OSError:
                pass
        paths_info.append({
            "path": str(wp),
            "available": exists,
            "file_count": file_count,
        })
    return {
        "running": True,
        "watch_paths": paths_info,
    }


# ---------------------------------------------------------------------------
# 4.2.1 GET /api/watcher/disk-usage
# ---------------------------------------------------------------------------

@router.get("/disk-usage")
def watcher_disk_usage() -> dict[str, Any]:
    return {"data": _disk_usage_for_watch_paths()}


# ---------------------------------------------------------------------------
# 4.3 GET /api/watcher/stats
# ---------------------------------------------------------------------------

@router.get("/stats")
def watcher_stats(conn: Connection = Depends(get_connection)) -> dict[str, Any]:
    now = now_utc8()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    def _stats_for_period(since: datetime) -> dict[str, Any]:
        base = select(
            watcher_events.c.event_type,
            func.count().label("cnt"),
        ).where(watcher_events.c.event_datetime >= since).group_by(watcher_events.c.event_type)
        rows = {r.event_type: r.cnt for r in conn.execute(base).all()}
        total = sum(rows.values())
        processed = rows.get("processed", 0)
        return {
            "total": total,
            "processed": processed,
            "failed": rows.get("failed", 0),
            "skipped": rows.get("skipped", 0),
            "success_rate": round(processed / total * 100, 1) if total else 0,
        }

    return {
        "today": _stats_for_period(today_start),
        "this_week": _stats_for_period(week_start),
    }


# ---------------------------------------------------------------------------
# 4.4 GET /api/watcher/events
# ---------------------------------------------------------------------------

@router.get("/events")
def watcher_events_list(
    event_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    filters = []
    if event_type:
        filters.append(watcher_events.c.event_type == event_type)

    where = and_(*filters) if filters else True

    total_stmt = select(func.count()).select_from(watcher_events).where(where)
    total = conn.execute(total_stmt).scalar_one()

    data_stmt = (
        select(watcher_events)
        .where(where)
        .order_by(watcher_events.c.event_datetime.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    rows = [
        {
            "id": r.id,
            "source_file": r.source_file,
            "event_type": r.event_type,
            "error_message": r.error_message,
            "event_datetime": r.event_datetime.isoformat() if r.event_datetime else None,
        }
        for r in conn.execute(data_stmt).all()
    ]
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


# ---------------------------------------------------------------------------
# 5.1 GET /api/watcher/files
# ---------------------------------------------------------------------------

@router.get("/files")
def watcher_files(
    status_filter: str | None = Query(None),
    path_filter: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    # Collect all recipe body files from watch paths
    all_files: list[dict[str, Any]] = []
    for wp in settings.watch_paths:
        rp = wp.resolve()
        if not rp.exists():
            continue
        if path_filter and not str(rp).startswith(path_filter) and not path_filter.startswith(str(rp)):
            continue
        try:
            for f in rp.rglob("*"):
                if not f.is_file() or not is_recipe_body_filename(f):
                    continue
                if path_filter and path_filter not in str(f):
                    continue
                try:
                    stat = f.stat()
                    all_files.append({
                        "path": str(f),
                        "size": stat.st_size,
                        "mtime": from_timestamp_utc8(stat.st_mtime).isoformat(),
                    })
                except OSError:
                    continue
        except OSError:
            continue

    # Sort by mtime desc
    all_files.sort(key=lambda x: x["mtime"], reverse=True)

    # Look up event status for these files from DB
    file_paths = [f["path"] for f in all_files]
    status_map: dict[str, dict[str, Any]] = {}
    if file_paths:
        # Get latest event per source_file
        latest = (
            select(
                watcher_events.c.source_file,
                func.max(watcher_events.c.event_datetime).label("latest_dt"),
            )
            .where(watcher_events.c.source_file.in_(file_paths))
            .group_by(watcher_events.c.source_file)
            .subquery()
        )
        stmt = (
            select(watcher_events)
            .join(
                latest,
                and_(
                    watcher_events.c.source_file == latest.c.source_file,
                    watcher_events.c.event_datetime == latest.c.latest_dt,
                ),
            )
        )
        for r in conn.execute(stmt).all():
            status_map[r.source_file] = {
                "status": r.event_type,
                "parsed_at": r.event_datetime.isoformat() if r.event_datetime else None,
                "error_message": r.error_message,
            }

    # Enrich files with status
    for f in all_files:
        info = status_map.get(f["path"])
        if info:
            f["status"] = info["status"]
            f["parsed_at"] = info["parsed_at"]
            f["error_message"] = info["error_message"]
        else:
            f["status"] = "pending"
            f["parsed_at"] = None
            f["error_message"] = None

    # Apply status filter
    if status_filter:
        all_files = [f for f in all_files if f["status"] == status_filter]

    total = len(all_files)
    start = (page - 1) * page_size
    page_data = all_files[start : start + page_size]

    return {"data": page_data, "total": total, "page": page, "page_size": page_size}


# ---------------------------------------------------------------------------
# 5.2 Path validation (used by other endpoints, exposed as helper above)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 6.1 POST /api/watcher/reparse
# ---------------------------------------------------------------------------

class ReparseRequest(BaseModel):
    source_files: list[str]


@router.post("/reparse")
def submit_reparse(
    body: ReparseRequest,
    conn: Connection = Depends(get_writable_connection),
    state_store=Depends(_get_state_store_dep),
) -> dict[str, Any]:
    if not body.source_files:
        raise HTTPException(status_code=400, detail="source_files must not be empty")

    # Validate all paths
    for sf in body.source_files:
        _validate_path_within_watch_paths(sf)

    # Clear FileStateStore entries
    if state_store:
        state_store.clear_many(body.source_files)

    # Create reparse task records
    now = now_utc8()
    task_ids = []
    for sf in body.source_files:
        payload = {
            "source_file": sf,
            "status": "pending",
            "created_at": now,
        }
        if conn.dialect.name == "sqlite":
            max_id = conn.execute(select(func.max(reparse_tasks.c.id))).scalar_one_or_none() or 0
            payload["id"] = int(max_id) + 1
        result = conn.execute(
            insert(reparse_tasks).values(
                **payload
            )
        )
        task_ids.append(int(result.inserted_primary_key[0]))

    return {"task_ids": task_ids, "total": len(task_ids)}


# ---------------------------------------------------------------------------
# 6.2 GET /api/watcher/reparse
# ---------------------------------------------------------------------------

@router.get("/reparse")
def get_reparse_status(
    task_ids: str | None = Query(None, description="Comma-separated task IDs"),
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    filters = []
    if task_ids:
        ids = [int(x.strip()) for x in task_ids.split(",") if x.strip()]
        if ids:
            filters.append(reparse_tasks.c.id.in_(ids))

    where = and_(*filters) if filters else True
    stmt = select(reparse_tasks).where(where).order_by(reparse_tasks.c.created_at.desc())
    rows = [
        {
            "id": r.id,
            "source_file": r.source_file,
            "status": r.status,
            "error_message": r.error_message,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in conn.execute(stmt).all()
    ]
    return {"data": rows, "total": len(rows)}


# ---------------------------------------------------------------------------
# 7.1 DELETE /api/watcher/files
# ---------------------------------------------------------------------------

class FileDeleteRequest(BaseModel):
    source_files: list[str]


@router.delete("/files")
def delete_files(
    body: FileDeleteRequest,
    conn: Connection = Depends(get_writable_connection),
    state_store=Depends(_get_state_store_dep),
) -> dict[str, Any]:
    if not body.source_files:
        raise HTTPException(status_code=400, detail="source_files must not be empty")

    results = []
    now = now_utc8()
    for sf in body.source_files:
        try:
            path = _validate_path_within_watch_paths(sf)
            stat = path.stat()
            file_size = stat.st_size
            file_mtime = from_timestamp_utc8(stat.st_mtime)
            path.unlink()

            # Clear state
            if state_store:
                state_store.clear(sf)

            # Log deletion
            _insert_with_pk_compat(
                conn,
                cleanup_log,
                {
                    "source_file": sf,
                    "file_size_bytes": file_size,
                    "file_mtime": file_mtime,
                    "deleted_at": now,
                    "trigger": "manual",
                },
            )
            results.append({"source_file": sf, "deleted": True})
        except HTTPException:
            results.append({"source_file": sf, "deleted": False, "error": "Invalid path"})
        except FileNotFoundError:
            results.append({"source_file": sf, "deleted": False, "error": "File not found"})
        except OSError as e:
            results.append({"source_file": sf, "deleted": False, "error": str(e)})

    return {"results": results}


# ---------------------------------------------------------------------------
# 7.2 GET /api/watcher/files/download
# ---------------------------------------------------------------------------

@router.get("/files/download")
def download_file(path: str = Query(...)) -> StreamingResponse:
    resolved = _validate_path_within_watch_paths(path)
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")

    filename = resolved.name + ".tar.gz"

    def _iter_file():
        with open(resolved, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(
        _iter_file(),
        media_type="application/gzip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# 9.1 GET/PUT /api/watcher/cleanup/config
# ---------------------------------------------------------------------------

@router.get("/cleanup/config")
def get_cleanup_config(conn: Connection = Depends(get_connection)) -> dict[str, Any]:
    row = _ensure_cleanup_config_row(conn)
    if row is None:
        return {"enabled": False, "threshold_percent": 80, "last_run_at": None, "updated_at": None}
    return {
        "enabled": bool(row.enabled),
        "threshold_percent": row.threshold_percent,
        "last_run_at": row.last_run_at.isoformat() if row.last_run_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


class CleanupConfigUpdate(BaseModel):
    enabled: bool
    threshold_percent: int


@router.put("/cleanup/config")
def update_cleanup_config(
    body: CleanupConfigUpdate,
    conn: Connection = Depends(get_writable_connection),
) -> dict[str, Any]:
    if not 1 <= body.threshold_percent <= 99:
        raise HTTPException(status_code=400, detail="threshold_percent must be 1-99")

    now = now_utc8()
    existing = _ensure_cleanup_config_row(conn)
    conn.execute(
        update(cleanup_config)
        .where(cleanup_config.c.id == existing.id)
        .values(
            enabled=body.enabled,
            threshold_percent=body.threshold_percent,
            updated_at=now,
        )
    )
    return {"enabled": body.enabled, "threshold_percent": body.threshold_percent}


# ---------------------------------------------------------------------------
# 9.5 GET /api/watcher/cleanup/log
# ---------------------------------------------------------------------------

@router.get("/cleanup/log")
def get_cleanup_log(
    trigger_filter: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    filters = []
    if trigger_filter:
        filters.append(cleanup_log.c.trigger == trigger_filter)

    where = and_(*filters) if filters else True

    total = conn.execute(select(func.count()).select_from(cleanup_log).where(where)).scalar_one()

    stmt = (
        select(cleanup_log)
        .where(where)
        .order_by(cleanup_log.c.deleted_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    rows = [
        {
            "id": r.id,
            "source_file": r.source_file,
            "file_size_bytes": r.file_size_bytes,
            "file_mtime": r.file_mtime.isoformat() if r.file_mtime else None,
            "deleted_at": r.deleted_at.isoformat() if r.deleted_at else None,
            "trigger": r.trigger,
        }
        for r in conn.execute(stmt).all()
    ]
    return {"data": rows, "total": total, "page": page, "page_size": page_size}
