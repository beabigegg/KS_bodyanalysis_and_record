from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC_PLUS_8 = timezone(timedelta(hours=8), name="UTC+8")


def now_utc8() -> datetime:
    """Return current UTC+8 time as naive datetime for DB DATETIME compatibility."""
    return datetime.now(UTC_PLUS_8).replace(tzinfo=None)


def from_timestamp_utc8(timestamp: float) -> datetime:
    """Convert POSIX timestamp to UTC+8 naive datetime."""
    return datetime.fromtimestamp(timestamp, tz=UTC_PLUS_8).replace(tzinfo=None)
