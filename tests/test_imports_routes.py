from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert
from sqlalchemy.pool import StaticPool


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT_DIR / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.schema import (  # noqa: E402
    metadata,
    recipe_app_spec,
    recipe_bsg,
    recipe_import,
    recipe_params,
    recipe_rpm_limits,
    recipe_rpm_reference,
    recipe_wir_group_map,
)
from deps import get_connection  # noqa: E402
from routes.imports import router  # noqa: E402


def _build_client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(
            insert(recipe_import).values(
                id=1,
                machine_type="ConnX Elite",
                machine_id="PJA3406",
                product_type="ECC17",
                bop="BOP-A",
                wafer_pn="WAF903898",
                recipe_version=1,
                recipe_name="Recipe-A",
                mc_serial="10626",
                sw_version="1.0",
                recipe_datetime=datetime(2026, 3, 24, 8, 0, 0),
                lot_id="LOT-1",
                source_file="sample.tar.gz",
                import_datetime=datetime(2026, 3, 25, 8, 30, 0),
            )
        )
        conn.execute(
            insert(recipe_params),
            [
                {
                    "id": 1,
                    "recipe_import_id": 1,
                    "file_type": "PRM",
                    "param_name": "parms/B1_Force_Seg_01",
                    "param_value": "150",
                    "unit": "grams",
                    "min_value": "100",
                    "max_value": "200",
                    "default_value": "150",
                },
                {
                    "id": 2,
                    "recipe_import_id": 1,
                    "file_type": "PRM",
                    "param_name": "parms/EFO_Power",
                    "param_value": "80",
                    "unit": None,
                    "min_value": None,
                    "max_value": None,
                    "default_value": None,
                },
                {
                    "id": 3,
                    "recipe_import_id": 1,
                    "file_type": "PHY",
                    "param_name": "mag_handler/IN_FIRST_SLOT",
                    "param_value": "1",
                    "unit": None,
                    "min_value": None,
                    "max_value": None,
                    "default_value": None,
                },
                {
                    "id": 4,
                    "recipe_import_id": 1,
                    "file_type": "LF",
                    "param_name": "LF_PITCH",
                    "param_value": "254.0",
                    "unit": None,
                    "min_value": None,
                    "max_value": None,
                    "default_value": None,
                },
                {
                    "id": 5,
                    "recipe_import_id": 1,
                    "file_type": "BSG",
                    "param_name": "ball_group_1.pbi_dia_nom",
                    "param_value": "5.0",
                    "unit": None,
                    "min_value": None,
                    "max_value": None,
                    "default_value": None,
                },
            ],
        )
        conn.execute(
            insert(recipe_app_spec).values(
                id=1,
                recipe_import_id=1,
                cap_manufacturer="K&S",
                wire_dia="1.7",
            )
        )
        conn.execute(
            insert(recipe_bsg),
            [
                {
                    "id": 1,
                    "recipe_import_id": 1,
                    "ball_group": "1",
                    "inspection_key": "pbi_dia_nom",
                    "process_key": "fab",
                    "value": "5.0",
                },
                {
                    "id": 2,
                    "recipe_import_id": 1,
                    "ball_group": "1",
                    "inspection_key": "pbi_height",
                    "process_key": "fab",
                    "value": "1.2",
                },
            ],
        )
        conn.execute(
            insert(recipe_rpm_limits).values(
                id=1,
                recipe_import_id=1,
                signal_name="sig-a",
                property_name="prop-a",
                rpm_group="grp",
                bond_type="ball",
                measurement_name="m1",
                limit_type="warning",
                statistic_type="avg",
                parameter_set="golden",
                lower_limit=0.1,
                upper_limit=0.9,
                active=True,
            )
        )
        conn.execute(
            insert(recipe_rpm_reference).values(
                id=1,
                recipe_import_id=1,
                signal_name="sig-a",
                property_name="prop-a",
                rpm_group="grp",
                bond_type="ball",
                measurement_name="m1",
                source="golden",
                average=0.5,
                median=0.5,
                std_dev=0.1,
                median_abs_dev=0.05,
                minimum=0.2,
                maximum=0.8,
                sample_count=10,
            )
        )
        conn.execute(
            insert(recipe_wir_group_map).values(
                id=1,
                recipe_import_id=1,
                parms_role="parms",
                wir_group_no=2,
                prm_stem="CJ621A20",
                wire_site_count=4,
            )
        )

    app = FastAPI()
    app.include_router(router)

    def override_get_connection():
        with engine.connect() as conn:
            yield conn

    app.dependency_overrides[get_connection] = override_get_connection
    return TestClient(app)


def test_import_summary_reports_section_counts() -> None:
    client = _build_client()

    response = client.get("/api/imports/1/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["params_total"] == 4
    assert payload["data"]["sections"] == {
        "has_app_spec": True,
        "bsg_rows": 2,
        "rpm_limits": 1,
        "rpm_reference": 1,
    }
    assert payload["data"]["file_types"] == [
        {"file_type": "LF", "count": 1},
        {"file_type": "PHY", "count": 1},
        {"file_type": "PRM", "count": 2},
    ]


def test_import_summary_returns_404_for_missing_import() -> None:
    client = _build_client()

    response = client.get("/api/imports/999/summary")

    assert response.status_code == 404


def test_param_facets_return_semantic_filter_values() -> None:
    client = _build_client()

    response = client.get("/api/imports/1/param-facets")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["file_types"] == [
        {"value": "LF", "count": 1},
        {"value": "PHY", "count": 1},
        {"value": "PRM", "count": 2},
    ]
    assert payload["param_groups_by_file_type"]["PRM"] == [{"value": "wire_2", "count": 2}]
    assert payload["param_groups_by_file_type"]["PHY"] == [{"value": "mag_handler", "count": 1}]
    assert payload["stages_by_file_type"]["PRM"] == [
        {"value": "bond1", "count": 2},
    ]
    assert payload["categories_by_file_type"]["PHY"] == [{"value": "slot", "count": 1}]


def test_get_import_params_pages_and_filters_semantic_rows() -> None:
    client = _build_client()

    response = client.get(
        "/api/imports/1/params",
        params={
            "file_type": "PRM",
            "param_group": "wire_2",
            "stage": "bond1",
            "category": "force",
            "page": 1,
            "page_size": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["data"]["page"] == 1
    assert payload["data"]["page_size"] == 1
    assert payload["data"]["total_pages"] == 1
    assert payload["data"]["rows"][0]["param_name"] == "parms/B1_Force_Seg_01"
    assert payload["data"]["rows"][0]["param_group"] == "wire_2"
    assert payload["data"]["rows"][0]["stage"] == "bond1"
    assert payload["data"]["rows"][0]["category"] == "force"


def test_get_import_params_excludes_raw_bsg_by_default() -> None:
    client = _build_client()

    response = client.get("/api/imports/1/params", params={"page_size": 20})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 4
    assert all(row["file_type"] != "BSG" for row in payload["data"]["rows"])
