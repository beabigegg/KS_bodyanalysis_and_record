from __future__ import annotations

import math
from statistics import mean, stdev
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import Connection, and_, distinct, select

from api.utils import row_to_dict
from deps import get_connection

from db.schema import recipe_import, recipe_params  # type: ignore[import-not-found]

router = APIRouter(prefix="/api/r2r", tags=["r2r"])


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_histogram(values: list[float], bins: int = 20) -> list[dict[str, float | int]]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if low == high:
        return [{"start": low, "end": high, "count": len(values)}]
    width = (high - low) / bins
    bucket_counts = [0] * bins
    for value in values:
        idx = min(int((value - low) / width), bins - 1)
        bucket_counts[idx] += 1
    output = []
    for idx, count in enumerate(bucket_counts):
        start = low + width * idx
        end = start + width
        output.append({"start": start, "end": end, "count": count})
    return output


def _compute_stats(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Compute SPC stats from a list of row dicts containing param_value, min_value, max_value."""
    values = [_to_float(row.get("param_value")) for row in rows]
    numeric_values = [v for v in values if v is not None]
    if not numeric_values:
        return None

    avg = mean(numeric_values)
    std_dev = stdev(numeric_values) if len(numeric_values) >= 2 else 0.0
    ucl = avg + 3 * std_dev
    lcl = avg - 3 * std_dev

    min_spec = next((_to_float(r.get("min_value")) for r in rows if _to_float(r.get("min_value")) is not None), None)
    max_spec = next((_to_float(r.get("max_value")) for r in rows if _to_float(r.get("max_value")) is not None), None)
    cp = None
    cpk = None
    if std_dev > 0 and min_spec is not None and max_spec is not None:
        cp = (max_spec - min_spec) / (6 * std_dev)
        cpk = min((max_spec - avg) / (3 * std_dev), (avg - min_spec) / (3 * std_dev))

    points = []
    for row in rows:
        value = _to_float(row.get("param_value"))
        if value is None:
            continue
        points.append(
            {
                "recipe_datetime": row.get("recipe_datetime"),
                "value": value,
                "out_of_control": value > ucl or value < lcl,
            }
        )

    return {
        "summary": {
            "mean": avg,
            "std_dev": std_dev,
            "ucl": ucl,
            "lcl": lcl,
            "cp": cp,
            "cpk": cpk,
            "count": len(numeric_values),
            "min_spec": min_spec,
            "max_spec": max_spec,
        },
        "points": points,
        "histogram": _build_histogram(numeric_values),
    }


@router.get("/stats")
def get_r2r_stats(
    machine_id: str,
    product_type: str,
    param_name: str,
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    stmt = (
        select(
            recipe_import.c.recipe_datetime,
            recipe_params.c.param_value,
            recipe_params.c.min_value,
            recipe_params.c.max_value,
            recipe_params.c.default_value,
        )
        .select_from(recipe_params.join(recipe_import, recipe_import.c.id == recipe_params.c.recipe_import_id))
        .where(
            and_(
                recipe_import.c.machine_id == machine_id,
                recipe_import.c.product_type == product_type,
                recipe_params.c.param_name == param_name,
            )
        )
        .order_by(recipe_import.c.recipe_datetime.asc())
    )

    rows = [row_to_dict(row) for row in conn.execute(stmt).all()]
    data = _compute_stats(rows)
    if not data:
        return {"data": None, "total": 0}
    return {"data": data, "total": len(data["points"])}


@router.get("/dashboard")
def get_r2r_dashboard(
    machine_id: str,
    product_type: str,
    watchlist: str | None = None,
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    watch = {item.strip() for item in (watchlist or "").split(",") if item.strip()}

    # Single query: fetch all param data for this machine+product at once
    stmt = (
        select(
            recipe_params.c.param_name,
            recipe_import.c.recipe_datetime,
            recipe_params.c.param_value,
            recipe_params.c.min_value,
            recipe_params.c.max_value,
        )
        .select_from(recipe_params.join(recipe_import, recipe_import.c.id == recipe_params.c.recipe_import_id))
        .where(
            and_(
                recipe_import.c.machine_id == machine_id,
                recipe_import.c.product_type == product_type,
            )
        )
        .order_by(recipe_params.c.param_name.asc(), recipe_import.c.recipe_datetime.asc())
    )
    all_rows = [row_to_dict(row) for row in conn.execute(stmt).all()]

    # Group by param_name
    from collections import defaultdict
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_rows:
        grouped[str(row["param_name"])].append(row)

    items = []
    for name, rows in grouped.items():
        data = _compute_stats(rows)
        if not data:
            continue
        summary = data["summary"]
        status = "normal"
        if summary["std_dev"] > 0:
            if summary["cpk"] is not None and summary["cpk"] < 1:
                status = "abnormal"
            elif summary["cpk"] is not None and summary["cpk"] < 1.33:
                status = "warning"
        items.append(
            {
                "param_name": name,
                "status": status,
                "is_watchlist": name in watch,
                "count": summary["count"],
                "cpk": summary["cpk"],
            }
        )
    items.sort(key=lambda x: (not x["is_watchlist"], x["status"], x["param_name"]))
    return {"data": items, "total": len(items)}


@router.get("/normal-curve")
def normal_curve(
    mean_value: float,
    std_dev: float,
    points: int = 100,
) -> dict[str, Any]:
    if std_dev <= 0:
        return {"data": [], "total": 0}
    start = mean_value - 4 * std_dev
    step = (8 * std_dev) / max(points - 1, 1)
    out = []
    for idx in range(points):
        x = start + idx * step
        y = (1.0 / (std_dev * math.sqrt(2 * math.pi))) * math.exp(
            -((x - mean_value) ** 2) / (2 * std_dev * std_dev)
        )
        out.append({"x": x, "y": y})
    return {"data": out, "total": len(out)}
