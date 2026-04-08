from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ksbody.config import get_settings

settings = get_settings()


@dataclass
class OracleClient:
    enabled: bool
    reason: str | None = None
    _conn: Any = None

    def connect(self) -> None:
        if settings.oracle is None:
            self.enabled = False
            self.reason = "Oracle connection not configured"
            return
        try:
            import oracledb  # type: ignore[import-not-found]
        except Exception:
            self.enabled = False
            self.reason = "oracledb driver not installed"
            return

        self._conn = oracledb.connect(
            user=settings.oracle.user,
            password=settings.oracle.password,
            dsn=settings.oracle.dsn,
        )
        self.enabled = True
        self.reason = None

    def fetch_yield_rows(
        self,
        machine_id: str,
        product_type: str,
        start_iso: str | None = None,
        end_iso: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.enabled or self._conn is None:
            return []

        sql = """
            SELECT machine_id, product_type, test_datetime, yield_value
            FROM ks_yield_records
            WHERE machine_id = :machine_id
              AND product_type = :product_type
              AND (:start_iso IS NULL OR test_datetime >= TO_DATE(:start_iso, 'YYYY-MM-DD"T"HH24:MI:SS'))
              AND (:end_iso IS NULL OR test_datetime <= TO_DATE(:end_iso, 'YYYY-MM-DD"T"HH24:MI:SS'))
            ORDER BY test_datetime
        """
        cursor = self._conn.cursor()
        cursor.execute(
            sql,
            machine_id=machine_id,
            product_type=product_type,
            start_iso=start_iso,
            end_iso=end_iso,
        )
        rows = []
        for machine, product, test_time, value in cursor:
            rows.append(
                {
                    "machine_id": machine,
                    "product_type": product,
                    "test_datetime": test_time.isoformat() if hasattr(test_time, "isoformat") else str(test_time),
                    "yield_value": float(value) if value is not None else None,
                }
            )
        return rows


oracle_client = OracleClient(enabled=False)
oracle_client.connect()