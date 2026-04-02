from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import unittest

from sqlalchemy import create_engine, insert

ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT_DIR / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.schema import (  # noqa: E402
    metadata,
    recipe_bsg,
    recipe_import,
    recipe_params,
    recipe_rpm_limits,
    recipe_rpm_reference,
)
from routes.compare import (  # noqa: E402
    CompareParamCatalogRequest,
    CompareParamKey,
    CompareRequest,
    compare_param_catalog,
    _diff_rows,
    _diff_rpm_rows,
    compare_recipe_params,
)


class CompareApplyChangeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        metadata.create_all(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def _insert_imports(self) -> None:
        rows = [
            {
                "id": 1,
                "machine_type": "ConnX",
                "machine_id": "M1",
                "product_type": "ECC17",
                "bop": "B1",
                "wafer_pn": "W1",
                "recipe_version": 1,
                "recipe_name": "R1",
                "mc_serial": "MC1",
                "sw_version": "1.0",
                "recipe_datetime": datetime(2026, 1, 1, 10, 0, 0),
                "source_file": "s1",
                "import_datetime": datetime(2026, 1, 1, 12, 0, 0),
            },
            {
                "id": 2,
                "machine_type": "ConnX",
                "machine_id": "M2",
                "product_type": "ECC17",
                "bop": "B1",
                "wafer_pn": "W1",
                "recipe_version": 1,
                "recipe_name": "R2",
                "mc_serial": "MC2",
                "sw_version": "1.0",
                "recipe_datetime": datetime(2026, 1, 1, 10, 0, 0),
                "source_file": "s2",
                "import_datetime": datetime(2026, 1, 1, 12, 0, 0),
            },
        ]
        with self.engine.begin() as conn:
            conn.execute(insert(recipe_import), rows)

    def test_diff_rows_marks_value_vs_none_as_diff(self) -> None:
        rows = [
            {
                "recipe_import_id": 1,
                "file_type": "PRM",
                "param_name": "Bond1_Force_Seg_01",
                "param_value": "150",
            }
        ]
        output = _diff_rows(["file_type", "param_name"], rows, [1, 2], show_all=False)

        self.assertEqual(len(output), 1)
        self.assertTrue(output[0]["is_diff"])
        self.assertEqual(output[0]["values"]["2"], None)

    def test_diff_rows_keeps_both_none_as_no_diff(self) -> None:
        rows = [
            {
                "recipe_import_id": 1,
                "file_type": "PRM",
                "param_name": "Bond1_Force_Seg_01",
                "param_value": None,
            },
            {
                "recipe_import_id": 2,
                "file_type": "PRM",
                "param_name": "Bond1_Force_Seg_01",
                "param_value": None,
            },
        ]
        output = _diff_rows(["file_type", "param_name"], rows, [1, 2], show_all=True)

        self.assertEqual(len(output), 1)
        self.assertFalse(output[0]["is_diff"])

    def test_diff_rpm_rows_supports_multi_field_output(self) -> None:
        keys = [
            "signal_name",
            "property_name",
            "rpm_group",
            "bond_type",
            "measurement_name",
            "limit_type",
            "statistic_type",
            "parameter_set",
        ]
        rows = [
            {
                "recipe_import_id": 1,
                "signal_name": "S1",
                "property_name": "P1",
                "rpm_group": "G1",
                "bond_type": "BT",
                "measurement_name": "M",
                "limit_type": "L",
                "statistic_type": "ST",
                "parameter_set": "PS",
                "lower_limit": 1.0,
                "upper_limit": 2.0,
                "active": True,
            }
        ]
        output = _diff_rpm_rows(keys, ["lower_limit", "upper_limit", "active"], rows, [1, 2], show_all=False)
        fields = {row["field"] for row in output}

        self.assertEqual(fields, {"lower_limit", "upper_limit", "active"})
        self.assertTrue(all(row["is_diff"] for row in output))

    def test_compare_excludes_bsg_from_params_and_includes_rpm_sections(self) -> None:
        self._insert_imports()
        with self.engine.begin() as conn:
            conn.execute(
                insert(recipe_params),
                [
                    {
                        "id": 1,
                        "recipe_import_id": 1,
                        "file_type": "PRM",
                        "param_name": "parms/B1_Force_Seg_01",
                        "param_value": "150",
                    },
                    {
                        "id": 2,
                        "recipe_import_id": 2,
                        "file_type": "PRM",
                        "param_name": "parms/B1_Force_Seg_01",
                        "param_value": "150",
                    },
                    {
                        "id": 3,
                        "recipe_import_id": 1,
                        "file_type": "BSG",
                        "param_name": "bsg_dup_key",
                        "param_value": "1",
                    },
                ],
            )
            conn.execute(
                insert(recipe_bsg),
                [
                    {
                        "id": 1,
                        "recipe_import_id": 1,
                        "ball_group": "BG1",
                        "inspection_key": "IK1",
                        "process_key": "PK1",
                        "value": "V1",
                    },
                    {
                        "id": 2,
                        "recipe_import_id": 2,
                        "ball_group": "BG1",
                        "inspection_key": "IK1",
                        "process_key": "PK1",
                        "value": "V2",
                    },
                ],
            )
            conn.execute(
                insert(recipe_rpm_limits),
                [
                    {
                        "id": 1,
                        "recipe_import_id": 1,
                        "signal_name": "S1",
                        "property_name": "P1",
                        "rpm_group": "G1",
                        "bond_type": "BT",
                        "measurement_name": "M1",
                        "limit_type": "L1",
                        "statistic_type": "ST1",
                        "parameter_set": "PS1",
                        "lower_limit": 1.0,
                        "upper_limit": 2.0,
                        "active": True,
                    }
                ],
            )
            conn.execute(
                insert(recipe_rpm_reference),
                [
                    {
                        "id": 1,
                        "recipe_import_id": 1,
                        "signal_name": "S1",
                        "property_name": "P1",
                        "rpm_group": "G1",
                        "bond_type": "BT",
                        "measurement_name": "M1",
                        "source": "SRC",
                        "average": 1.0,
                        "median": 1.0,
                        "std_dev": 0.1,
                        "median_abs_dev": 0.05,
                        "minimum": 0.8,
                        "maximum": 1.2,
                        "sample_count": 12,
                    }
                ],
            )

        payload = CompareRequest(import_ids=[1, 2], section="params", show_all=True, page=1, page_size=10)
        with self.engine.connect() as conn:
            result = compare_recipe_params(payload, conn)

        data = result["data"]
        self.assertEqual(data["section"], "params")
        self.assertTrue(all(row["file_type"] != "BSG" for row in data["rows"]))
        self.assertEqual(data["rows"][0]["stage"], "bond1")
        self.assertEqual(data["rows"][0]["category"], "force")
        self.assertEqual(data["total_rows"], 1)
        self.assertEqual(data["total_pages"], 1)

        bsg_payload = CompareRequest(import_ids=[1, 2], section="bsg", show_all=True, page=1, page_size=10)
        with self.engine.connect() as conn:
            bsg_result = compare_recipe_params(bsg_payload, conn)
        self.assertEqual(bsg_result["data"]["section"], "bsg")
        self.assertTrue(all("stage" not in row and "category" not in row for row in bsg_result["data"]["rows"]))
        self.assertGreater(len(bsg_result["data"]["rows"]), 0)

        rpm_limits_payload = CompareRequest(
            import_ids=[1, 2],
            section="rpm_limits",
            show_all=True,
            page=1,
            page_size=10,
        )
        rpm_reference_payload = CompareRequest(
            import_ids=[1, 2],
            section="rpm_reference",
            show_all=True,
            page=1,
            page_size=10,
        )
        with self.engine.connect() as conn:
            rpm_limits_result = compare_recipe_params(rpm_limits_payload, conn)
            rpm_reference_result = compare_recipe_params(rpm_reference_payload, conn)
        self.assertGreater(len(rpm_limits_result["data"]["rows"]), 0)
        self.assertGreater(len(rpm_reference_result["data"]["rows"]), 0)

    def test_compare_response_pages_rows(self) -> None:
        self._insert_imports()
        with self.engine.begin() as conn:
            conn.execute(
                insert(recipe_params),
                [
                    {
                        "id": 1,
                        "recipe_import_id": 1,
                        "file_type": "PRM",
                        "param_name": "parms/B1_Force_Seg_01",
                        "param_value": "150",
                    },
                    {
                        "id": 2,
                        "recipe_import_id": 2,
                        "file_type": "PRM",
                        "param_name": "parms/B1_Force_Seg_01",
                        "param_value": "151",
                    },
                    {
                        "id": 3,
                        "recipe_import_id": 1,
                        "file_type": "PRM",
                        "param_name": "parms/B2_Time_Seg_01",
                        "param_value": "20",
                    },
                    {
                        "id": 4,
                        "recipe_import_id": 2,
                        "file_type": "PRM",
                        "param_name": "parms/B2_Time_Seg_01",
                        "param_value": "22",
                    },
                ],
            )

        payload = CompareRequest(import_ids=[1, 2], section="params", show_all=False, page=1, page_size=1)
        with self.engine.connect() as conn:
            result = compare_recipe_params(payload, conn)

        data = result["data"]
        self.assertEqual(data["section"], "params")
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 1)
        self.assertEqual(data["total_rows"], 2)
        self.assertEqual(data["total_pages"], 2)
        self.assertEqual(len(data["rows"]), 1)

    def test_compare_param_catalog_includes_facets_and_partial_presence(self) -> None:
        self._insert_imports()
        with self.engine.begin() as conn:
            conn.execute(
                insert(recipe_params),
                [
                    {
                        "id": 1,
                        "recipe_import_id": 1,
                        "file_type": "PRM",
                        "param_name": "parms/B1_Force_Seg_01",
                        "param_value": "150",
                    },
                    {
                        "id": 2,
                        "recipe_import_id": 2,
                        "file_type": "PRM",
                        "param_name": "parms/B1_Force_Seg_01",
                        "param_value": "151",
                    },
                    {
                        "id": 3,
                        "recipe_import_id": 1,
                        "file_type": "PRM",
                        "param_name": "parms/B2_Time_Seg_01",
                        "param_value": "20",
                    },
                    {
                        "id": 4,
                        "recipe_import_id": 2,
                        "file_type": "PHY",
                        "param_name": "phy/Some_Param",
                        "param_value": "1",
                    },
                ],
            )

        payload = CompareParamCatalogRequest(import_ids=[1, 2], page=1, page_size=10)
        with self.engine.connect() as conn:
            result = compare_param_catalog(payload, conn)

        data = result["data"]
        self.assertEqual(data["total_rows"], 3)
        self.assertEqual(data["facets"]["file_types"][0]["value"], "PHY")
        self.assertEqual(data["facets"]["file_types"][1]["value"], "PRM")
        partial_row = next(row for row in data["rows"] if row["param_name"] == "parms/B2_Time_Seg_01")
        self.assertEqual(partial_row["present_count"], 1)
        self.assertEqual(partial_row["missing_count"], 1)
        self.assertTrue(partial_row["is_partial_presence"])

        filtered_payload = CompareParamCatalogRequest(import_ids=[1, 2], file_type="PRM", page=1, page_size=10)
        with self.engine.connect() as conn:
            filtered_result = compare_param_catalog(filtered_payload, conn)
        filtered_data = filtered_result["data"]
        self.assertTrue(all(row["file_type"] == "PRM" for row in filtered_data["rows"]))
        self.assertEqual(
            {entry["value"] for entry in filtered_data["facets"]["file_types"]},
            {"PRM", "PHY"},
        )

    def test_compare_params_section_can_be_scoped_to_selected_keys(self) -> None:
        self._insert_imports()
        with self.engine.begin() as conn:
            conn.execute(
                insert(recipe_params),
                [
                    {
                        "id": 1,
                        "recipe_import_id": 1,
                        "file_type": "PRM",
                        "param_name": "parms/B1_Force_Seg_01",
                        "param_value": "150",
                    },
                    {
                        "id": 2,
                        "recipe_import_id": 2,
                        "file_type": "PRM",
                        "param_name": "parms/B1_Force_Seg_01",
                        "param_value": "151",
                    },
                    {
                        "id": 3,
                        "recipe_import_id": 1,
                        "file_type": "PRM",
                        "param_name": "parms/B2_Time_Seg_01",
                        "param_value": "20",
                    },
                    {
                        "id": 4,
                        "recipe_import_id": 2,
                        "file_type": "PRM",
                        "param_name": "parms/B2_Time_Seg_01",
                        "param_value": "22",
                    },
                ],
            )

        payload = CompareRequest(
            import_ids=[1, 2],
            section="params",
            show_all=True,
            selected_params=[CompareParamKey(file_type="PRM", param_name="parms/B2_Time_Seg_01")],
            page=1,
            page_size=10,
        )
        with self.engine.connect() as conn:
            result = compare_recipe_params(payload, conn)

        rows = result["data"]["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["file_type"], "PRM")
        self.assertEqual(rows[0]["param_name"], "parms/B2_Time_Seg_01")


if __name__ == "__main__":
    unittest.main()
