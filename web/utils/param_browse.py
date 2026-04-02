from __future__ import annotations

from typing import Any

from utils.param_classifier import ParamClassifier


def facet_items(counter: dict[str, int], *, sort_alpha: bool = True) -> list[dict[str, Any]]:
    items = [{"value": key, "count": count} for key, count in counter.items()]
    if sort_alpha:
        items.sort(key=lambda item: str(item["value"]))
    else:
        items.sort(key=lambda item: (-int(item["count"]), str(item["value"])))
    return items


def param_role(param_name: str) -> str | None:
    if "/" not in param_name:
        return None
    role = param_name.split("/", 1)[0].strip()
    return role or None


def param_group(
    param_name: str,
    wire_group_map: dict[str, int] | None = None,
) -> str | None:
    role = param_role(param_name)
    if role is None:
        return None
    if role.startswith("parms") and wire_group_map is not None:
        wire_group_no = wire_group_map.get(role)
        if wire_group_no is not None:
            return f"wire_{wire_group_no}"
    return role


def semantic_param_item(
    item: dict[str, Any],
    *,
    wire_group_map: dict[str, int] | None = None,
) -> dict[str, Any]:
    param_name = str(item.get("param_name") or "")
    file_type = str(item.get("file_type") or "")
    semantics = ParamClassifier.classify_semantics(param_name, file_type)
    item["param_group"] = param_group(param_name, wire_group_map)
    item.update(semantics.as_dict())
    return item
