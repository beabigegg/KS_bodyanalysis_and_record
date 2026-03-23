from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BIGINT,
    BOOLEAN,
    DATETIME,
    FLOAT,
    INTEGER,
    TEXT,
    VARCHAR,
    Column,
    ForeignKey,
    Index,
    MetaData,
    Table,
)

metadata = MetaData()

recipe_import = Table(
    "ksbody_recipe_import",
    metadata,
    Column("id", BIGINT, primary_key=True, autoincrement=True),
    Column("machine_type", VARCHAR(128), nullable=False),
    Column("machine_id", VARCHAR(128), nullable=False),
    Column("product_type", VARCHAR(128), nullable=False),
    Column("bop", VARCHAR(128), nullable=False),
    Column("wafer_pn", VARCHAR(128), nullable=False),
    Column("recipe_version", INTEGER, nullable=False),
    Column("recipe_name", VARCHAR(255), nullable=True),
    Column("mc_serial", VARCHAR(128), nullable=True),
    Column("sw_version", VARCHAR(128), nullable=True),
    Column("recipe_datetime", DATETIME, nullable=True),
    Column("lot_id", VARCHAR(128), nullable=True),
    Column("source_file", VARCHAR(1024), nullable=False),
    Column("import_datetime", DATETIME, nullable=False, default=datetime.utcnow),
)

Index(
    "idx_ksbody_import_product_machine",
    recipe_import.c.product_type,
    recipe_import.c.bop,
    recipe_import.c.wafer_pn,
    recipe_import.c.machine_id,
)
Index(
    "idx_ksbody_import_time_series",
    recipe_import.c.machine_id,
    recipe_import.c.product_type,
    recipe_import.c.recipe_datetime,
)

recipe_params = Table(
    "ksbody_recipe_params",
    metadata,
    Column("id", BIGINT, primary_key=True, autoincrement=True),
    Column("recipe_import_id", BIGINT, ForeignKey("ksbody_recipe_import.id"), nullable=False),
    Column("file_type", VARCHAR(32), nullable=False),
    Column("param_name", VARCHAR(255), nullable=False),
    Column("param_value", TEXT, nullable=True),
    Column("unit", VARCHAR(64), nullable=True),
    Column("min_value", VARCHAR(128), nullable=True),
    Column("max_value", VARCHAR(128), nullable=True),
    Column("default_value", VARCHAR(128), nullable=True),
)

Index(
    "idx_ksbody_params_lookup",
    recipe_params.c.recipe_import_id,
    recipe_params.c.file_type,
    recipe_params.c.param_name,
)

recipe_app_spec = Table(
    "ksbody_recipe_app_spec",
    metadata,
    Column("id", BIGINT, primary_key=True, autoincrement=True),
    Column("recipe_import_id", BIGINT, ForeignKey("ksbody_recipe_import.id"), nullable=False),
    Column("cap_manufacturer", VARCHAR(128), nullable=True),
    Column("cap_part_number", VARCHAR(128), nullable=True),
    Column("cap_tip_dia", VARCHAR(64), nullable=True),
    Column("cap_hole_dia", VARCHAR(64), nullable=True),
    Column("chamfer_dia", VARCHAR(64), nullable=True),
    Column("inner_cone_angle", VARCHAR(64), nullable=True),
    Column("face_angle", VARCHAR(64), nullable=True),
    Column("wire_manufacturer", VARCHAR(128), nullable=True),
    Column("wire_part_number", VARCHAR(128), nullable=True),
    Column("wire_dia", VARCHAR(64), nullable=True),
    Column("wire_metal", VARCHAR(64), nullable=True),
)

Index("idx_ksbody_app_spec_import", recipe_app_spec.c.recipe_import_id, unique=True)

recipe_bsg = Table(
    "ksbody_recipe_bsg",
    metadata,
    Column("id", BIGINT, primary_key=True, autoincrement=True),
    Column("recipe_import_id", BIGINT, ForeignKey("ksbody_recipe_import.id"), nullable=False),
    Column("ball_group", VARCHAR(64), nullable=False),
    Column("inspection_key", VARCHAR(128), nullable=False),
    Column("process_key", VARCHAR(128), nullable=True),
    Column("value", TEXT, nullable=True),
)

Index("idx_ksbody_bsg_import", recipe_bsg.c.recipe_import_id)

recipe_rpm_limits = Table(
    "ksbody_recipe_rpm_limits",
    metadata,
    Column("id", BIGINT, primary_key=True, autoincrement=True),
    Column("recipe_import_id", BIGINT, ForeignKey("ksbody_recipe_import.id"), nullable=False),
    Column("signal_name", VARCHAR(128), nullable=False),
    Column("property_name", VARCHAR(128), nullable=False),
    Column("rpm_group", VARCHAR(64), nullable=True),
    Column("bond_type", VARCHAR(64), nullable=True),
    Column("measurement_name", VARCHAR(128), nullable=True),
    Column("limit_type", VARCHAR(64), nullable=True),
    Column("statistic_type", VARCHAR(64), nullable=True),
    Column("parameter_set", VARCHAR(64), nullable=True),
    Column("lower_limit", FLOAT, nullable=True),
    Column("upper_limit", FLOAT, nullable=True),
    Column("active", BOOLEAN, nullable=True),
)

Index("idx_ksbody_rpm_limits_import", recipe_rpm_limits.c.recipe_import_id)

recipe_rpm_reference = Table(
    "ksbody_recipe_rpm_reference",
    metadata,
    Column("id", BIGINT, primary_key=True, autoincrement=True),
    Column("recipe_import_id", BIGINT, ForeignKey("ksbody_recipe_import.id"), nullable=False),
    Column("signal_name", VARCHAR(128), nullable=False),
    Column("property_name", VARCHAR(128), nullable=False),
    Column("rpm_group", VARCHAR(64), nullable=True),
    Column("bond_type", VARCHAR(64), nullable=True),
    Column("measurement_name", VARCHAR(128), nullable=True),
    Column("source", VARCHAR(64), nullable=True),
    Column("average", FLOAT, nullable=True),
    Column("median", FLOAT, nullable=True),
    Column("std_dev", FLOAT, nullable=True),
    Column("median_abs_dev", FLOAT, nullable=True),
    Column("minimum", FLOAT, nullable=True),
    Column("maximum", FLOAT, nullable=True),
    Column("sample_count", INTEGER, nullable=True),
)

Index("idx_ksbody_rpm_reference_import", recipe_rpm_reference.c.recipe_import_id)

ALL_TABLES = [
    recipe_import,
    recipe_params,
    recipe_app_spec,
    recipe_bsg,
    recipe_rpm_limits,
    recipe_rpm_reference,
]
