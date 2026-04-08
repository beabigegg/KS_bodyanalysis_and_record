from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any


def jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def row_to_dict(row: Any) -> dict[str, Any]:
    return {key: jsonable(val) for key, val in row._mapping.items()}

