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
    recipe_wir_group_map,
)

router = APIRouter(prefix="/api/compare", tags=["compare"])


def _fetch_wir_group_map(
    conn: Connection,
    import_ids: list[int],
) -> dict[tuple[int, str], int]:
    """Return {(import_id, parms_role): wir_group_no} for the given imports."""
    stmt = select(recipe_wir_group_map).where(
        recipe_wir_group_map.c.recipe_import_id.in_(import_ids)
    )
    result: dict[tuple[int, str], int] = {}
    for row in conn.execute(stmt).all():
        d = row_to_dict(row)
        result[(int(d["recipe_import_id"]), str(d["parms_role"]))] = int(d["wir_group_no"])
    return result


class CompareRequest(BaseModel):
    import_ids: list[int] = Field(min_length=2, max_length=20, description="Import IDs to compare.")
    section: str = Field(default="params", description="Active compare section.")
    file_type: str | None = None
    show_all: bool = Field(default=False, description="When true, include non-diff rows.")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=200, ge=1, le=1000)


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
    wir_group_map: dict[tuple[int, str], int] | None = None,
) -> list[dict[str, Any]]:
    """Build pivoted diff rows from source_rows.

    include_classification: when True, each row is enriched with ``stage``,
    ``category``, ``param_group``, and ``wir_group_no`` fields.  For parms_N
    groups, diff is computed only across imports that actually have that group,
    so machines without a particular group do not count as a value difference.
    """
    # Pre-compute which parms groups each import owns (used for group-aware diff).
    parms_groups_per_import: dict[int, set[str]] = {}
    if include_classification:
        parms_groups_per_import = {imp_id: set() for imp_id in import_ids}
        for row in source_rows:
            imp_id = int(row["recipe_import_id"])
            pn = str(row.get("param_name") or "")
            role = pn.split("/")[0] if "/" in pn else ""
            if role.startswith("parms"):
                parms_groups_per_import[imp_id].add(role)

    pivot: dict[tuple[Any, ...], dict[int, Any]] = defaultdict(dict)
    for row in source_rows:
        key = tuple(row.get(k) for k in keys)
        pivot[key][int(row["recipe_import_id"])] = row.get("param_value", row.get("value"))

    output: list[dict[str, Any]] = []
    for key, val_map in pivot.items():
        item = {k: key[idx] for idx, k in enumerate(keys)}

        # Determine param_group early so diff can be group-scoped.
        param_group: str | None = None
        if include_classification:
            pn = str(item.get("param_name") or "")
            role = pn.split("/")[0] if "/" in pn else ""
            param_group = role if role.startswith("parms") else None

        # For parms_N groups: only compare imports that own this group.
        if param_group is not None:
            relevant_ids = [
                imp_id for imp_id in import_ids
                if param_group in parms_groups_per_import.get(imp_id, set())
            ]
        else:
            relevant_ids = import_ids

        values = [val_map.get(imp_id) for imp_id in relevant_ids]
        is_diff = _has_diff(values)
        if not show_all and not is_diff:
            continue

        item["values"] = {str(import_id): val_map.get(import_id) for import_id in import_ids}
        item["is_diff"] = is_diff
        if include_classification:
            item["param_group"] = param_group
            stage, category = ParamClassifier.classify(
                str(item.get("param_name") or ""),
                str(item.get("file_type") or ""),
            )
            item["stage"] = stage
            item["category"] = category
            wir_group_no: int | None = None
            if wir_group_map is not None and param_group is not None:
                for imp_id in import_ids:
                    v = wir_group_map.get((imp_id, param_group))
                    if v is not None:
                        wir_group_no = v
                        break
            item["wir_group_no"] = wir_group_no
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


def _paginate_rows(
    rows: list[dict[str, Any]],
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int, int]:
    total_rows = len(rows)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    start = (page - 1) * page_size
    return rows[start : start + page_size], total_rows, total_pages


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

    section = payload.section.lower()
    if section not in {"params", "app_spec", "bsg", "rpm_limits", "rpm_reference"}:
        raise HTTPException(status_code=422, detail="Unsupported compare section")

    wgm = _fetch_wir_group_map(conn, payload.import_ids)
    wgm_stmt = select(recipe_wir_group_map).where(
        recipe_wir_group_map.c.recipe_import_id.in_(payload.import_ids)
    )
    wire_group_context: dict[str, list[dict[str, Any]]] = {
        str(imp_id): [] for imp_id in payload.import_ids
    }
    for row in conn.execute(wgm_stmt).all():
        d = row_to_dict(row)
        key = str(int(d["recipe_import_id"]))
        wire_group_context[key].append(
            {
                "parms_role": d["parms_role"],
                "wir_group_no": d["wir_group_no"],
                "prm_stem": d.get("prm_stem"),
                "wire_site_count": d.get("wire_site_count"),
            }
        )

    section_rows: list[dict[str, Any]]
    if section == "params":
        param_stmt = (
            select(recipe_params)
            .where(recipe_params.c.recipe_import_id.in_(payload.import_ids))
            .where(recipe_params.c.file_type != "BSG")
        )
        if payload.file_type:
            param_stmt = param_stmt.where(recipe_params.c.file_type.ilike(f"%{payload.file_type}%"))
        param_rows = [row_to_dict(row) for row in conn.execute(param_stmt).all()]
        section_rows = _diff_rows(
            ["file_type", "param_name"],
            param_rows,
            payload.import_ids,
            payload.show_all,
            include_classification=True,
            wir_group_map=wgm,
        )
    elif section == "app_spec":
        app_stmt = select(recipe_app_spec).where(recipe_app_spec.c.recipe_import_id.in_(payload.import_ids))
        app_rows = [row_to_dict(row) for row in conn.execute(app_stmt).all()]
        app_pivot: list[dict[str, Any]] = []
        app_columns = [c.name for c in recipe_app_spec.columns if c.name not in {"id", "recipe_import_id"}]
        for column in app_columns:
            values = {str(int(row["recipe_import_id"])): row.get(column) for row in app_rows}
            is_diff = _has_diff(list(values.values()))
            if payload.show_all or is_diff:
                app_pivot.append({"field": column, "values": values, "is_diff": is_diff})
        section_rows = app_pivot
    elif section == "bsg":
        bsg_stmt = select(recipe_bsg).where(recipe_bsg.c.recipe_import_id.in_(payload.import_ids))
        bsg_rows = [row_to_dict(row) for row in conn.execute(bsg_stmt).all()]
        section_rows = _diff_rows(
            ["ball_group", "inspection_key", "process_key"],
            bsg_rows,
            payload.import_ids,
            payload.show_all,
        )
    elif section == "rpm_limits":
        rpm_limit_stmt = select(recipe_rpm_limits).where(recipe_rpm_limits.c.recipe_import_id.in_(payload.import_ids))
        rpm_limit_rows = [row_to_dict(row) for row in conn.execute(rpm_limit_stmt).all()]
        section_rows = _diff_rpm_rows(
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
    else:
        rpm_reference_stmt = select(recipe_rpm_reference).where(
            recipe_rpm_reference.c.recipe_import_id.in_(payload.import_ids)
        )
        rpm_reference_rows = [row_to_dict(row) for row in conn.execute(rpm_reference_stmt).all()]
        section_rows = _diff_rpm_rows(
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

    paged_rows, total_rows, total_pages = _paginate_rows(section_rows, payload.page, payload.page_size)

    return {
        "data": {
            "imports": imports,
            "section": section,
            "rows": paged_rows,
            "page": payload.page,
            "page_size": payload.page_size,
            "total_pages": total_pages,
            "total_rows": total_rows,
            "wire_group_context": wire_group_context,
        },
        "total": total_rows,
    }
