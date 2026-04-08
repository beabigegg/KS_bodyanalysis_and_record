from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import Engine, create_engine, delete, func, insert, select, update

from ksbody.config import Settings
from ksbody.db.schema import (
    recipe_app_spec,
    recipe_bsg,
    recipe_import,
    recipe_params,
    recipe_rpm_limits,
    recipe_rpm_reference,
    recipe_wir_group_map,
    watcher_events,
)
from ksbody.timeutils import now_utc8


class RecipeRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @classmethod
    def from_settings(cls, settings: Settings) -> "RecipeRepository":
        engine = create_engine(settings.mysql.sqlalchemy_url(), future=True)
        return cls(engine)

    def save_recipe(
        self,
        import_record: Mapping[str, Any],
        params: Sequence[Mapping[str, Any]],
        app_spec: Mapping[str, Any] | None,
        bsg_rows: Sequence[Mapping[str, Any]],
        rpm_limits: Sequence[Mapping[str, Any]],
        rpm_reference: Sequence[Mapping[str, Any]],
        wir_group_map: Sequence[Mapping[str, Any]] | None = None,
    ) -> int:
        with self.engine.begin() as conn:
            payload = dict(import_record)
            payload.setdefault("import_datetime", now_utc8())
            result = conn.execute(insert(recipe_import).values(**payload))
            recipe_import_id = int(result.inserted_primary_key[0])

            if params:
                clean_params = []
                for row in params:
                    r = {**row, "recipe_import_id": recipe_import_id}
                    pn = r.get("param_name") or ""
                    if not pn.isprintable() or len(pn) > 1024:
                        continue
                    clean_params.append(r)
                if clean_params:
                    conn.execute(insert(recipe_params), clean_params)

            if app_spec:
                conn.execute(
                    insert(recipe_app_spec).values(
                        **dict(app_spec), recipe_import_id=recipe_import_id
                    )
                )

            if bsg_rows:
                clean_bsg = []
                for row in bsg_rows:
                    r = {**row, "recipe_import_id": recipe_import_id}
                    # Skip rows with binary/non-printable data in keys
                    pk = r.get("process_key") or ""
                    ik = r.get("inspection_key") or ""
                    if not pk.isprintable() or not ik.isprintable():
                        continue
                    # Truncate to column limits
                    if len(pk) > 255:
                        r["process_key"] = pk[:255]
                    if len(ik) > 255:
                        r["inspection_key"] = ik[:255]
                    clean_bsg.append(r)
                if clean_bsg:
                    conn.execute(insert(recipe_bsg), clean_bsg)

            if rpm_limits:
                conn.execute(
                    insert(recipe_rpm_limits),
                    [{**row, "recipe_import_id": recipe_import_id} for row in rpm_limits],
                )

            if rpm_reference:
                conn.execute(
                    insert(recipe_rpm_reference),
                    [{**row, "recipe_import_id": recipe_import_id} for row in rpm_reference],
                )

            if wir_group_map:
                conn.execute(
                    insert(recipe_wir_group_map),
                    [{**row, "recipe_import_id": recipe_import_id} for row in wir_group_map],
                )

            return recipe_import_id

    def get_last_import_epoch(self, source_file: str) -> float:
        with self.engine.connect() as conn:
            stmt = select(func.max(recipe_import.c.import_datetime)).where(
                recipe_import.c.source_file == source_file
            )
            value = conn.execute(stmt).scalar_one_or_none()
            if value is None:
                return 0.0
            if hasattr(value, "timestamp"):
                return float(value.timestamp())
            return 0.0


class WatcherEventRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def record_event(
        self,
        source_file: str,
        event_type: str,
        error_message: str | None = None,
    ) -> int:
        with self.engine.begin() as conn:
            payload: dict[str, Any] = {
                "source_file": source_file,
                "event_type": event_type,
                "error_message": error_message,
                "event_datetime": now_utc8(),
            }
            if conn.dialect.name == "sqlite":
                max_id = conn.execute(select(func.max(watcher_events.c.id))).scalar_one_or_none() or 0
                payload["id"] = int(max_id) + 1
            result = conn.execute(
                insert(watcher_events).values(**payload)
            )
            return int(result.inserted_primary_key[0])
