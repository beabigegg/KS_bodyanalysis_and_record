from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any

from ksbody.pipeline.parsers.base import BaseParser, ParseResult


class SqliteParser(BaseParser):
    """Parse RPM SQLite databases into limits/reference datasets."""

    REFERENCE_TABLES = [
        "rpm_reference_data",
        "rpm_reference_data_current",
        "rpm_reference_data_golden",
        "rpm_reference_data_local",
    ]

    def parse(self, file_path: str | Path) -> ParseResult:
        path = Path(file_path)
        file_type = path.suffix.lstrip(".").upper()
        result = ParseResult(file_type=file_type)

        conn = sqlite3.connect(path)
        try:
            conn.row_factory = sqlite3.Row
            result.rpm_limits = self._extract_limits(conn)
            result.rpm_reference = self._extract_reference(conn)
        finally:
            conn.close()

        return result

    def _extract_limits(self, conn: sqlite3.Connection) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        if self._table_exists(conn, "rpm_limits"):
            query = """
                SELECT
                    signal_name_k,
                    property_name_k,
                    rpm_group_k,
                    bond_type_k,
                    measurement_name_k,
                    limit_type_k,
                    statistic_type_k,
                    NULL AS parameter_set,
                    lower_limit,
                    upper_limit,
                    CASE
                        WHEN COALESCE(lower_active, 0) = 1 OR COALESCE(upper_active, 0) = 1 THEN 1
                        ELSE 0
                    END AS active
                FROM rpm_limits
            """
            rows.extend(self._fetch_limits(conn, query))

        if not rows and self._table_exists(conn, "rpm_warning_limits"):
            query = """
                SELECT
                    signal_name_k,
                    property_name_k,
                    rpm_group_k,
                    bond_type_k,
                    measurement_name_k,
                    'warning' AS limit_type_k,
                    NULL AS statistic_type_k,
                    NULL AS parameter_set,
                    lower_limit,
                    upper_limit,
                    CASE
                        WHEN COALESCE(lower_active, 0) = 1 OR COALESCE(upper_active, 0) = 1 THEN 1
                        ELSE 0
                    END AS active
                FROM rpm_warning_limits
            """
            rows.extend(self._fetch_limits(conn, query))

        return rows

    def _fetch_limits(
        self, conn: sqlite3.Connection, query: str
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for row in conn.execute(query):
            result.append(
                {
                    "signal_name": row["signal_name_k"],
                    "property_name": row["property_name_k"],
                    "rpm_group": row["rpm_group_k"],
                    "bond_type": row["bond_type_k"],
                    "measurement_name": row["measurement_name_k"],
                    "limit_type": row["limit_type_k"],
                    "statistic_type": row["statistic_type_k"],
                    "parameter_set": row["parameter_set"],
                    "lower_limit": self._to_float(row["lower_limit"]),
                    "upper_limit": self._to_float(row["upper_limit"]),
                    "active": bool(row["active"]),
                }
            )
        return result

    def _extract_reference(self, conn: sqlite3.Connection) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()

        for table in self.REFERENCE_TABLES:
            if not self._table_exists(conn, table):
                continue

            query = f"""
                SELECT
                    signal_name_k,
                    property_name_k,
                    rpm_group_k,
                    bond_type_k,
                    measurement_name_k,
                    source_k,
                    average,
                    median,
                    std_dev,
                    median_abs_dev,
                    minimum,
                    maximum,
                    sample_count
                FROM {table}
            """
            for row in conn.execute(query):
                key = (
                    row["signal_name_k"],
                    row["property_name_k"],
                    row["rpm_group_k"],
                    row["bond_type_k"],
                    row["measurement_name_k"],
                    row["source_k"],
                    row["average"],
                    row["median"],
                    row["std_dev"],
                    row["median_abs_dev"],
                    row["minimum"],
                    row["maximum"],
                    row["sample_count"],
                )
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "signal_name": row["signal_name_k"],
                        "property_name": row["property_name_k"],
                        "rpm_group": row["rpm_group_k"],
                        "bond_type": row["bond_type_k"],
                        "measurement_name": row["measurement_name_k"],
                        "source": row["source_k"],
                        "average": self._to_float(row["average"]),
                        "median": self._to_float(row["median"]),
                        "std_dev": self._to_float(row["std_dev"]),
                        "median_abs_dev": self._to_float(row["median_abs_dev"]),
                        "minimum": self._to_float(row["minimum"]),
                        "maximum": self._to_float(row["maximum"]),
                        "sample_count": self._to_int(row["sample_count"]),
                    }
                )

        return rows

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
        query = "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1"
        return conn.execute(query, (table_name,)).fetchone() is not None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
