from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Connection, and_, distinct, func, or_, select

from utils import row_to_dict
from deps import get_connection

from db.schema import (  # type: ignore[import-not-found]
    recipe_app_spec,
    recipe_bsg,
    recipe_import,
    recipe_params,
    recipe_rpm_limits,
    recipe_rpm_reference,
)

router = APIRouter(prefix="/api/imports", tags=["imports"])


@router.get("/filter-options")
def filter_options(conn: Connection = Depends(get_connection)) -> dict[str, Any]:
    machine_types = [row[0] for row in conn.execute(select(distinct(recipe_import.c.machine_type)).order_by(recipe_import.c.machine_type)).all()]
    machine_ids = [row[0] for row in conn.execute(select(distinct(recipe_import.c.machine_id)).order_by(recipe_import.c.machine_id)).all()]
    product_types = [row[0] for row in conn.execute(select(distinct(recipe_import.c.product_type)).order_by(recipe_import.c.product_type)).all()]
    return {
        "data": {
            "machine_types": machine_types,
            "machine_ids": machine_ids,
            "product_types": product_types,
        },
        "total": 1,
    }


@router.get("")
def list_imports(
    machine_type: str | None = None,
    machine_id: str | None = None,
    product_type: str | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    filters = []
    if machine_type:
        filters.append(recipe_import.c.machine_type == machine_type)
    if machine_id:
        filters.append(recipe_import.c.machine_id == machine_id)
    if product_type:
        filters.append(recipe_import.c.product_type == product_type)
    if search:
        term = f"%{search}%"
        filters.append(
            or_(
                recipe_import.c.product_type.like(term),
                recipe_import.c.bop.like(term),
                recipe_import.c.wafer_pn.like(term),
                recipe_import.c.recipe_name.like(term),
            )
        )

    where_clause = and_(*filters) if filters else None
    count_stmt = select(func.count()).select_from(recipe_import)
    if where_clause is not None:
        count_stmt = count_stmt.where(where_clause)
    total = int(conn.execute(count_stmt).scalar_one())

    stmt = select(recipe_import).order_by(recipe_import.c.import_datetime.desc())
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    rows = conn.execute(stmt).all()

    return {
        "data": [row_to_dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{import_id}/params")
def get_import_params(
    import_id: int,
    search: str | None = None,
    file_type: str | None = None,
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    check_stmt = select(recipe_import.c.id).where(recipe_import.c.id == import_id)
    if conn.execute(check_stmt).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Import record not found")

    filters = [recipe_params.c.recipe_import_id == import_id]
    if file_type:
        filters.append(recipe_params.c.file_type == file_type)
    if search:
        filters.append(recipe_params.c.param_name.like(f"%{search}%"))

    stmt = (
        select(recipe_params)
        .where(and_(*filters))
        .order_by(recipe_params.c.file_type.asc(), recipe_params.c.param_name.asc())
    )
    rows = conn.execute(stmt).all()

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        item = row_to_dict(row)
        grouped[str(item["file_type"])].append(item)

    return {
        "data": grouped,
        "total": len(rows),
    }


@router.get("/{import_id}/app-spec")
def get_app_spec(import_id: int, conn: Connection = Depends(get_connection)) -> dict[str, Any]:
    stmt = select(recipe_app_spec).where(recipe_app_spec.c.recipe_import_id == import_id)
    row = conn.execute(stmt).first()
    return {"data": row_to_dict(row) if row else None, "total": 1 if row else 0}


@router.get("/{import_id}/bsg")
def get_bsg(import_id: int, conn: Connection = Depends(get_connection)) -> dict[str, Any]:
    stmt = (
        select(recipe_bsg)
        .where(recipe_bsg.c.recipe_import_id == import_id)
        .order_by(recipe_bsg.c.ball_group.asc(), recipe_bsg.c.inspection_key.asc())
    )
    rows = conn.execute(stmt).all()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        item = row_to_dict(row)
        grouped[str(item["ball_group"])].append(item)
    return {"data": grouped, "total": len(rows)}


@router.get("/{import_id}/rpm")
def get_rpm(import_id: int, conn: Connection = Depends(get_connection)) -> dict[str, Any]:
    limit_stmt = (
        select(recipe_rpm_limits)
        .where(recipe_rpm_limits.c.recipe_import_id == import_id)
        .order_by(recipe_rpm_limits.c.signal_name.asc(), recipe_rpm_limits.c.property_name.asc())
    )
    ref_stmt = (
        select(recipe_rpm_reference)
        .where(recipe_rpm_reference.c.recipe_import_id == import_id)
        .order_by(recipe_rpm_reference.c.signal_name.asc(), recipe_rpm_reference.c.property_name.asc())
    )
    limits = [row_to_dict(row) for row in conn.execute(limit_stmt).all()]
    references = [row_to_dict(row) for row in conn.execute(ref_stmt).all()]
    return {
        "data": {
            "limits": limits,
            "reference": references,
        },
        "total": len(limits) + len(references),
    }

