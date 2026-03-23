from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import Connection, and_, select

from api.utils import row_to_dict
from deps import get_connection
from services.oracle_conn import oracle_client

from db.schema import recipe_import, recipe_params  # type: ignore[import-not-found]

router = APIRouter(prefix="/api/yield-correlation", tags=["yield-correlation"])


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@router.get("/status")
def oracle_status() -> dict[str, Any]:
    return {
        "data": {
            "configured": oracle_client.enabled,
            "message": oracle_client.reason or "Oracle connection is ready",
        },
        "total": 1,
    }


@router.get("/query")
def query_yield_correlation(
    machine_id: str,
    product_type: str,
    param_name: str,
    window_minutes: int = 120,
    start: datetime | None = None,
    end: datetime | None = None,
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    param_stmt = (
        select(
            recipe_import.c.recipe_datetime,
            recipe_params.c.param_value,
        )
        .where(
            and_(
                recipe_import.c.id == recipe_params.c.recipe_import_id,
                recipe_import.c.machine_id == machine_id,
                recipe_import.c.product_type == product_type,
                recipe_params.c.param_name == param_name,
            )
        )
        .order_by(recipe_import.c.recipe_datetime.asc())
    )
    if start:
        param_stmt = param_stmt.where(recipe_import.c.recipe_datetime >= start)
    if end:
        param_stmt = param_stmt.where(recipe_import.c.recipe_datetime <= end)

    params = [row_to_dict(row) for row in conn.execute(param_stmt).all()]
    yield_rows = oracle_client.fetch_yield_rows(
        machine_id=machine_id,
        product_type=product_type,
        start_iso=start.isoformat() if start else None,
        end_iso=end.isoformat() if end else None,
    )

    if not oracle_client.enabled:
        return {
            "data": {
                "configured": False,
                "message": oracle_client.reason or "Oracle connection not configured",
                "trend": [],
                "scatter": [],
            },
            "total": 0,
        }

    parsed_yield = []
    for row in yield_rows:
        test_time = datetime.fromisoformat(str(row["test_datetime"]))
        parsed_yield.append({**row, "test_dt": test_time})

    trend = []
    scatter = []
    for param in params:
        recipe_time_raw = param.get("recipe_datetime")
        if not recipe_time_raw:
            continue
        recipe_time = datetime.fromisoformat(str(recipe_time_raw))
        param_value = _to_float(param.get("param_value"))
        if param_value is None:
            continue
        win = timedelta(minutes=window_minutes)
        matched = [
            row
            for row in parsed_yield
            if abs(row["test_dt"] - recipe_time) <= win and row.get("yield_value") is not None
        ]
        if not matched:
            continue
        avg_yield = sum(float(row["yield_value"]) for row in matched) / len(matched)
        trend.append(
            {
                "recipe_datetime": recipe_time.isoformat(),
                "param_value": param_value,
                "yield_value": avg_yield,
            }
        )
        scatter.append({"x": param_value, "y": avg_yield})

    return {
        "data": {
            "configured": True,
            "trend": trend,
            "scatter": scatter,
        },
        "total": len(trend),
    }
