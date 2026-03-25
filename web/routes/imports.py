from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Connection, and_, distinct, func, or_, select

from utils import row_to_dict
from utils.param_classifier import ParamClassifier
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


def _ensure_import_exists(conn: Connection, import_id: int) -> None:
    stmt = select(recipe_import.c.id).where(recipe_import.c.id == import_id)
    if conn.execute(stmt).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Import record not found")


def _param_group(param_name: str) -> str | None:
    if "/" not in param_name:
        return None
    group = param_name.split("/", 1)[0].strip()
    return group or None


def _semantic_param_row(row: Any) -> dict[str, Any]:
    item = row_to_dict(row)
    param_name = str(item.get("param_name") or "")
    file_type = str(item.get("file_type") or "")
    stage, category = ParamClassifier.classify(param_name, file_type)
    item["param_group"] = _param_group(param_name)
    item["stage"] = stage
    item["category"] = category
    return item


def _load_semantic_params(
    conn: Connection,
    import_id: int,
    *,
    search: str | None = None,
    file_type: str | None = None,
) -> list[dict[str, Any]]:
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
    return [_semantic_param_row(row) for row in conn.execute(stmt).all()]


def _facet_items(counter: dict[str, int], *, sort_alpha: bool = True) -> list[dict[str, Any]]:
    items = [{"value": key, "count": count} for key, count in counter.items()]
    if sort_alpha:
        items.sort(key=lambda item: str(item["value"]))
    else:
        items.sort(key=lambda item: (-int(item["count"]), str(item["value"])))
    return items


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

    return {
        "data": {
            "file_types": _facet_items(file_type_counts),
            "param_groups_by_file_type": {
                key: _facet_items(dict(value))
                for key, value in sorted(param_groups_by_type.items())
            },
            "stages_by_file_type": {
                key: _facet_items(dict(value))
                for key, value in sorted(stages_by_type.items())
            },
            "categories_by_file_type": {
                key: _facet_items(dict(value))
                for key, value in sorted(categories_by_type.items())
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
