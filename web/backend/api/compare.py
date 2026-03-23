from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, select

from api.utils import row_to_dict
from deps import get_connection

from db.schema import (  # type: ignore[import-not-found]
    recipe_app_spec,
    recipe_bsg,
    recipe_import,
    recipe_params,
)

router = APIRouter(prefix="/api/compare", tags=["compare"])


class CompareRequest(BaseModel):
    import_ids: list[int] = Field(min_length=2, max_length=20)
    file_type: str | None = None
    show_all: bool = False


def _diff_rows(
    keys: list[str],
    source_rows: list[dict[str, Any]],
    import_ids: list[int],
    show_all: bool,
) -> list[dict[str, Any]]:
    pivot: dict[tuple[Any, ...], dict[int, Any]] = defaultdict(dict)
    for row in source_rows:
        key = tuple(row.get(k) for k in keys)
        pivot[key][int(row["recipe_import_id"])] = row.get("param_value", row.get("value"))

    output: list[dict[str, Any]] = []
    for key, val_map in pivot.items():
        values = [val_map.get(import_id) for import_id in import_ids]
        is_diff = len({str(value) for value in values if value is not None}) > 1
        if not show_all and not is_diff:
            continue
        item = {k: key[idx] for idx, k in enumerate(keys)}
        item["values"] = {str(import_id): val_map.get(import_id) for import_id in import_ids}
        item["is_diff"] = is_diff
        output.append(item)
    return output


@router.post("")
def compare_recipe_params(
    payload: CompareRequest,
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    meta_stmt = (
        select(recipe_import)
        .where(recipe_import.c.id.in_(payload.import_ids))
        .order_by(recipe_import.c.machine_id.asc())
    )
    imports = [row_to_dict(row) for row in conn.execute(meta_stmt).all()]
    if len(imports) != len(payload.import_ids):
        raise HTTPException(status_code=404, detail="One or more import records do not exist")

    param_stmt = select(recipe_params).where(recipe_params.c.recipe_import_id.in_(payload.import_ids))
    if payload.file_type:
        param_stmt = param_stmt.where(recipe_params.c.file_type == payload.file_type)
    param_rows = [row_to_dict(row) for row in conn.execute(param_stmt).all()]
    param_diff = _diff_rows(["file_type", "param_name"], param_rows, payload.import_ids, payload.show_all)

    app_stmt = select(recipe_app_spec).where(recipe_app_spec.c.recipe_import_id.in_(payload.import_ids))
    app_rows = [row_to_dict(row) for row in conn.execute(app_stmt).all()]
    app_pivot: list[dict[str, Any]] = []
    app_columns = [c.name for c in recipe_app_spec.columns if c.name not in {"id", "recipe_import_id"}]
    for column in app_columns:
        values = {str(int(row["recipe_import_id"])): row.get(column) for row in app_rows}
        is_diff = len({str(val) for val in values.values() if val is not None}) > 1
        if payload.show_all or is_diff:
            app_pivot.append({"field": column, "values": values, "is_diff": is_diff})

    bsg_stmt = select(recipe_bsg).where(recipe_bsg.c.recipe_import_id.in_(payload.import_ids))
    bsg_rows = [row_to_dict(row) for row in conn.execute(bsg_stmt).all()]
    bsg_diff = _diff_rows(
        ["ball_group", "inspection_key", "process_key"],
        bsg_rows,
        payload.import_ids,
        payload.show_all,
    )

    return {
        "data": {
            "imports": imports,
            "params": param_diff,
            "app_spec": app_pivot,
            "bsg": bsg_diff,
        },
        "total": len(param_diff),
    }

