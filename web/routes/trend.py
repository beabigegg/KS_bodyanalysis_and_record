from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Connection, and_, select

from utils import row_to_dict
from deps import get_connection

from db.schema import recipe_import, recipe_params  # type: ignore[import-not-found]

router = APIRouter(prefix="/api/trend", tags=["trend"])


def _parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@router.get("")
def get_trend(
    machine_id: str | None = None,
    product_type: str | None = None,
    bop: str | None = None,
    wafer_pn: str | None = None,
    param_name: str = Query(...),
    machines: str | None = None,
    params: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    machine_ids = _parse_csv(machines) or ([machine_id] if machine_id else [])
    param_names = _parse_csv(params) or [param_name]

    filters = [
        recipe_params.c.param_name.in_(param_names),
        recipe_import.c.id == recipe_params.c.recipe_import_id,
    ]
    if machine_ids:
        filters.append(recipe_import.c.machine_id.in_(machine_ids))
    if product_type:
        filters.append(recipe_import.c.product_type == product_type)
    if bop:
        filters.append(recipe_import.c.bop == bop)
    if wafer_pn:
        filters.append(recipe_import.c.wafer_pn == wafer_pn)
    if start:
        filters.append(recipe_import.c.recipe_datetime >= start)
    if end:
        filters.append(recipe_import.c.recipe_datetime <= end)

    stmt = (
        select(
            recipe_import.c.id.label("import_id"),
            recipe_import.c.machine_id,
            recipe_import.c.product_type,
            recipe_import.c.bop,
            recipe_import.c.wafer_pn,
            recipe_import.c.recipe_datetime,
            recipe_params.c.file_type,
            recipe_params.c.param_name,
            recipe_params.c.param_value,
            recipe_params.c.min_value,
            recipe_params.c.max_value,
            recipe_params.c.default_value,
        )
        .where(and_(*filters))
        .order_by(recipe_import.c.recipe_datetime.asc())
    )

    rows = [row_to_dict(row) for row in conn.execute(stmt).all()]
    series: dict[str, list[dict[str, Any]]] = defaultdict(list)
    refs: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = f"{row['machine_id']}::{row['param_name']}"
        series[key].append(row)
        refs.setdefault(
            key,
            {
                "min_value": row.get("min_value"),
                "max_value": row.get("max_value"),
                "default_value": row.get("default_value"),
            },
        )

    return {
        "data": {
            "series": [{"key": key, "points": points, "reference": refs.get(key)} for key, points in series.items()],
        },
        "total": len(rows),
    }

