from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import Connection, and_, delete, distinct, func, or_, select

from utils import row_to_dict
from utils.param_browse import facet_items, semantic_param_item
from deps import get_connection, get_writable_connection

from db.schema import (  # type: ignore[import-not-found]
    recipe_app_spec,
    recipe_bsg,
    recipe_import,
    recipe_params,
    recipe_rpm_limits,
    recipe_rpm_reference,
    recipe_wir_group_map,
)

router = APIRouter(prefix="/api/imports", tags=["imports"])

_CHILD_TABLES = [
    recipe_params,
    recipe_app_spec,
    recipe_bsg,
    recipe_rpm_limits,
    recipe_rpm_reference,
    recipe_wir_group_map,
]


class BatchDeleteRequest(BaseModel):
    ids: list[int]


def _ensure_import_exists(conn: Connection, import_id: int) -> None:
    stmt = select(recipe_import.c.id).where(recipe_import.c.id == import_id)
    if conn.execute(stmt).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Import record not found")


def _fetch_wir_group_map(conn: Connection, import_id: int) -> dict[str, int]:
    stmt = select(recipe_wir_group_map).where(recipe_wir_group_map.c.recipe_import_id == import_id)
    result: dict[str, int] = {}
    for row in conn.execute(stmt).all():
        data = row_to_dict(row)
        result[str(data["parms_role"])] = int(data["wir_group_no"])
    return result


def _semantic_param_row(row: Any, wire_group_map: dict[str, int]) -> dict[str, Any]:
    return semantic_param_item(row_to_dict(row), wire_group_map=wire_group_map)


def _load_semantic_params(
    conn: Connection,
    import_id: int,
    *,
    search: str | None = None,
    file_type: str | None = None,
) -> list[dict[str, Any]]:
    wire_group_map = _fetch_wir_group_map(conn, import_id)
    filters = [recipe_params.c.recipe_import_id == import_id]
    if file_type:
        filters.append(recipe_params.c.file_type == file_type)
    else:
        filters.append(recipe_params.c.file_type != "BSG")
    if search:
        filters.append(recipe_params.c.param_name.like(f"%{search}%"))

    stmt = (
        select(recipe_params)
        .where(and_(*filters))
        .order_by(
            recipe_params.c.file_type.asc(),
            recipe_params.c.param_name.asc(),
            recipe_params.c.id.asc(),
        )
    )
    return [_semantic_param_row(row, wire_group_map) for row in conn.execute(stmt).all()]


@router.get("/{import_id}/summary")
def get_import_summary(import_id: int, conn: Connection = Depends(get_connection)) -> dict[str, Any]:
    _ensure_import_exists(conn, import_id)

    params_total_stmt = (
        select(func.count())
        .select_from(recipe_params)
        .where(
            and_(
                recipe_params.c.recipe_import_id == import_id,
                recipe_params.c.file_type != "BSG",
            )
        )
    )
    file_type_stmt = (
        select(recipe_params.c.file_type, func.count().label("count"))
        .where(
            and_(
                recipe_params.c.recipe_import_id == import_id,
                recipe_params.c.file_type != "BSG",
            )
        )
        .group_by(recipe_params.c.file_type)
        .order_by(recipe_params.c.file_type.asc())
    )
    app_exists_stmt = (
        select(func.count())
        .select_from(recipe_app_spec)
        .where(recipe_app_spec.c.recipe_import_id == import_id)
    )
    bsg_count_stmt = (
        select(func.count()).select_from(recipe_bsg).where(recipe_bsg.c.recipe_import_id == import_id)
    )
    rpm_limits_stmt = (
        select(func.count())
        .select_from(recipe_rpm_limits)
        .where(recipe_rpm_limits.c.recipe_import_id == import_id)
    )
    rpm_reference_stmt = (
        select(func.count())
        .select_from(recipe_rpm_reference)
        .where(recipe_rpm_reference.c.recipe_import_id == import_id)
    )

    file_types = [
        {"file_type": str(row[0]), "count": int(row[1])}
        for row in conn.execute(file_type_stmt).all()
    ]

    return {
        "data": {
            "import_id": import_id,
            "params_total": int(conn.execute(params_total_stmt).scalar_one()),
            "file_types": file_types,
            "sections": {
                "has_app_spec": bool(conn.execute(app_exists_stmt).scalar_one()),
                "bsg_rows": int(conn.execute(bsg_count_stmt).scalar_one()),
                "rpm_limits": int(conn.execute(rpm_limits_stmt).scalar_one()),
                "rpm_reference": int(conn.execute(rpm_reference_stmt).scalar_one()),
            },
        },
        "total": 1,
    }


@router.get("/{import_id}/param-facets")
def get_import_param_facets(import_id: int, conn: Connection = Depends(get_connection)) -> dict[str, Any]:
    _ensure_import_exists(conn, import_id)
    rows = _load_semantic_params(conn, import_id)

    file_type_counts: dict[str, int] = defaultdict(int)
    param_groups_by_type: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    stages_by_type: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    categories_by_type: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    families_by_type: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    features_by_type: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in rows:
        file_type = str(row["file_type"])
        file_type_counts[file_type] += 1

        param_group = row.get("param_group")
        if isinstance(param_group, str) and param_group:
            param_groups_by_type[file_type][param_group] += 1

        stage = row.get("stage")
        if isinstance(stage, str) and stage:
            stages_by_type[file_type][stage] += 1

        category = row.get("category")
        if isinstance(category, str) and category:
            categories_by_type[file_type][category] += 1

        family = row.get("family")
        if isinstance(family, str) and family:
            families_by_type[file_type][family] += 1

        feature = row.get("feature")
        if isinstance(feature, str) and feature:
            features_by_type[file_type][feature] += 1

    return {
        "data": {
            "file_types": facet_items(file_type_counts),
            "param_groups_by_file_type": {
                key: facet_items(dict(value))
                for key, value in sorted(param_groups_by_type.items())
            },
            "stages_by_file_type": {
                key: facet_items(dict(value))
                for key, value in sorted(stages_by_type.items())
            },
            "categories_by_file_type": {
                key: facet_items(dict(value))
                for key, value in sorted(categories_by_type.items())
            },
            "families_by_file_type": {
                key: facet_items(dict(value))
                for key, value in sorted(families_by_type.items())
            },
            "features_by_file_type": {
                key: facet_items(dict(value))
                for key, value in sorted(features_by_type.items())
            },
        },
        "total": len(rows),
    }


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
    param_group: str | None = None,
    stage: str | None = None,
    category: str | None = None,
    family: str | None = None,
    feature: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    _ensure_import_exists(conn, import_id)
    rows = _load_semantic_params(conn, import_id, search=search, file_type=file_type)

    if param_group:
        rows = [row for row in rows if row.get("param_group") == param_group]
    if stage:
        rows = [row for row in rows if row.get("stage") == stage]
    if category:
        rows = [row for row in rows if row.get("category") == category]
    if family:
        rows = [row for row in rows if row.get("family") == family]
    if feature:
        rows = [row for row in rows if row.get("feature") == feature]

    total = len(rows)
    start = (page - 1) * page_size
    paged_rows = rows[start : start + page_size]

    return {
        "data": {
            "rows": paged_rows,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        },
        "total": total,
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


@router.delete("/batch")
def delete_imports_batch(
    body: BatchDeleteRequest,
    conn: Connection = Depends(get_writable_connection),
) -> dict[str, Any]:
    if not body.ids:
        raise HTTPException(status_code=400, detail="ids list must not be empty")
    for table in _CHILD_TABLES:
        conn.execute(delete(table).where(table.c.recipe_import_id.in_(body.ids)))
    result = conn.execute(delete(recipe_import).where(recipe_import.c.id.in_(body.ids)))
    return {"data": {"deleted": result.rowcount}, "total": 1}


@router.delete("/{import_id}")
def delete_import(import_id: int, conn: Connection = Depends(get_writable_connection)) -> dict[str, Any]:
    if conn.execute(select(recipe_import.c.id).where(recipe_import.c.id == import_id)).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Import record not found")
    for table in _CHILD_TABLES:
        conn.execute(delete(table).where(table.c.recipe_import_id == import_id))
    conn.execute(delete(recipe_import).where(recipe_import.c.id == import_id))
    return {"data": {"deleted": 1}, "total": 1}


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
