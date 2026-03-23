from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Engine, create_engine, func, insert, select

from config.settings import AppSettings
from db.schema import (
    recipe_app_spec,
    recipe_bsg,
    recipe_import,
    recipe_params,
    recipe_rpm_limits,
    recipe_rpm_reference,
)


class RecipeRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "RecipeRepository":
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
    ) -> int:
        with self.engine.begin() as conn:
            payload = dict(import_record)
            payload.setdefault("import_datetime", datetime.utcnow())
            result = conn.execute(insert(recipe_import).values(**payload))
            recipe_import_id = int(result.inserted_primary_key[0])

            if params:
                conn.execute(
                    insert(recipe_params),
                    [{**row, "recipe_import_id": recipe_import_id} for row in params],
                )

            if app_spec:
                conn.execute(
                    insert(recipe_app_spec).values(
                        **dict(app_spec), recipe_import_id=recipe_import_id
                    )
                )

            if bsg_rows:
                conn.execute(
                    insert(recipe_bsg),
                    [{**row, "recipe_import_id": recipe_import_id} for row in bsg_rows],
                )

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
