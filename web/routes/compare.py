from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, select

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

router = APIRouter(prefix="/api/compare", tags=["compare"])


class CompareRequest(BaseModel):
    import_ids: list[int] = Field(min_length=2, max_length=20, description="Import IDs to compare.")
    file_type: str | None = None
    show_all: bool = Field(default=False, description="When true, include non-diff rows.")


def _has_diff(values: list[Any]) -> bool:
    non_null_values = {str(value) for value in values if value is not None}
    has_any_value = len(non_null_values) > 0
    all_have_value = all(value is not None for value in values)
    return len(non_null_values) > 1 or (has_any_value and not all_have_value)


def _diff_rows(
    keys: list[str],
    source_rows: list[dict[str, Any]],
    import_ids: list[int],
    show_all: bool,
    include_classification: bool = False,
) -> list[dict[str, Any]]:
    """Build pivoted diff rows from source_rows.

    include_classification: when True, each row is enriched with ``stage`` and
    ``category`` fields via ParamClassifier.  Only param rows need this; other
    diff sections (app_spec, bsg, rpm_*) should leave this False.
    """
    pivot: dict[tuple[Any, ...], dict[int, Any]] = defaultdict(dict)
    for row in source_rows:
        key = tuple(row.get(k) for k in keys)
        pivot[key][int(row["recipe_import_id"])] = row.get("param_value", row.get("value"))

    output: list[dict[str, Any]] = []
    for key, val_map in pivot.items():
        values = [val_map.get(import_id) for import_id in import_ids]
        is_diff = _has_diff(values)
        if not show_all and not is_diff:
            continue
        item = {k: key[idx] for idx, k in enumerate(keys)}
        item["values"] = {str(import_id): val_map.get(import_id) for import_id in import_ids}
        item["is_diff"] = is_diff
        if include_classification:
            stage, category = ParamClassifier.classify(
                str(item.get("param_name") or ""),
                str(item.get("file_type") or ""),
            )
            item["stage"] = stage
            item["category"] = category
        output.append(item)
    return output


def _diff_rpm_rows(
    keys: list[str],
    value_fields: list[str],
    source_rows: list[dict[str, Any]],
    import_ids: list[int],
    show_all: bool,
) -> list[dict[str, Any]]:
    pivot: dict[tuple[Any, ...], dict[str, dict[int, Any]]] = defaultdict(lambda: defaultdict(dict))

    for row in source_rows:
        key = tuple(row.get(k) for k in keys)
        recipe_import_id = int(row["recipe_import_id"])
        for field in value_fields:
            pivot[key][field][recipe_import_id] = row.get(field)

    output: list[dict[str, Any]] = []
    sorted_keys = sorted(pivot.keys(), key=lambda key: tuple("" if v is None else str(v) for v in key))
    for key in sorted_keys:
        key_item = {k: key[idx] for idx, k in enumerate(keys)}
        for field in value_fields:
            val_map = pivot[key].get(field, {})
            values = [val_map.get(import_id) for import_id in import_ids]
            is_diff = _has_diff(values)
            if not show_all and not is_diff:
                continue
            output.append(
                {
                    **key_item,
                    "field": field,
                    "values": {str(import_id): val_map.get(import_id) for import_id in import_ids},
                    "is_diff": is_diff,
                }
            )
    return output


@router.post("")
def compare_recipe_params(
    payload: CompareRequest,
    conn: Connection = Depends(get_connection),
) -> dict[str, Any]:
    """
    Compare selected imports.

    Response data includes params/app_spec/bsg, plus:
    - rpm_limits: CompareRow[] (expanded per value field)
    - rpm_reference: CompareRow[] (expanded per value field)
    """
    meta_stmt = (
        select(recipe_import)
        .where(recipe_import.c.id.in_(payload.import_ids))
        .order_by(recipe_import.c.machine_id.asc())
    )
    imports = [row_to_dict(row) for row in conn.execute(meta_stmt).all()]
    if len(imports) != len(payload.import_ids):
        raise HTTPException(status_code=404, detail="One or more import records do not exist")

    param_stmt = (
        select(recipe_params)
        .where(recipe_params.c.recipe_import_id.in_(payload.import_ids))
        .where(recipe_params.c.file_type != "BSG")
    )
    if payload.file_type:
        param_stmt = param_stmt.where(recipe_params.c.file_type == payload.file_type)
    param_rows = [row_to_dict(row) for row in conn.execute(param_stmt).all()]
    param_diff = _diff_rows(
        ["file_type", "param_name"],
        param_rows,
        payload.import_ids,
        payload.show_all,
        include_classification=True,
    )

    app_stmt = select(recipe_app_spec).where(recipe_app_spec.c.recipe_import_id.in_(payload.import_ids))
    app_rows = [row_to_dict(row) for row in conn.execute(app_stmt).all()]
    app_pivot: list[dict[str, Any]] = []
    app_columns = [c.name for c in recipe_app_spec.columns if c.name not in {"id", "recipe_import_id"}]
    for column in app_columns:
        values = {str(int(row["recipe_import_id"])): row.get(column) for row in app_rows}
        is_diff = _has_diff(list(values.values()))
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

    rpm_limit_stmt = select(recipe_rpm_limits).where(recipe_rpm_limits.c.recipe_import_id.in_(payload.import_ids))
    rpm_limit_rows = [row_to_dict(row) for row in conn.execute(rpm_limit_stmt).all()]
    rpm_limits_diff = _diff_rpm_rows(
        [
            "signal_name",
            "property_name",
            "rpm_group",
            "bond_type",
            "measurement_name",
            "limit_type",
            "statistic_type",
            "parameter_set",
        ],
        ["lower_limit", "upper_limit", "active"],
        rpm_limit_rows,
        payload.import_ids,
        payload.show_all,
    )

    rpm_reference_stmt = select(recipe_rpm_reference).where(
        recipe_rpm_reference.c.recipe_import_id.in_(payload.import_ids)
    )
    rpm_reference_rows = [row_to_dict(row) for row in conn.execute(rpm_reference_stmt).all()]
    rpm_reference_diff = _diff_rpm_rows(
        [
            "signal_name",
            "property_name",
            "rpm_group",
            "bond_type",
            "measurement_name",
            "source",
        ],
        ["average", "median", "std_dev", "median_abs_dev", "minimum", "maximum", "sample_count"],
        rpm_reference_rows,
        payload.import_ids,
        payload.show_all,
    )

    return {
        "data": {
            "imports": imports,
            "params": param_diff,
            "app_spec": app_pivot,
            "bsg": bsg_diff,
            "rpm_limits": rpm_limits_diff,
            "rpm_reference": rpm_reference_diff,
        },
        "total": len(param_diff),
    }
