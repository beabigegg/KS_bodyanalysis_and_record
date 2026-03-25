from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT_DIR / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline import RecipePipeline  # noqa: E402
from utils.param_classifier import ParamClassifier  # noqa: E402


class ParamClassifierTests(unittest.TestCase):
    class _MetadataStub:
        def to_dict(self) -> dict[str, object]:
            return {
                "machine_type": "ConnX Elite",
                "machine_id": "MC-01",
                "product_type": "ECC17",
                "bop": "BOP-A",
                "wafer_pn": "WAF903898",
                "recipe_version": 1,
            }

    class _Repo:
        def __init__(self) -> None:
            self.saved: dict[str, object] | None = None

        def save_recipe(self, **kwargs: object) -> int:
            self.saved = dict(kwargs)
            return 1

    def test_prm_bond1_force_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/B1_Force_Seg_01", "PRM")
        self.assertEqual((stage, category), ("bond1", "force"))

    def test_prm_bond1_common_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/B1_Contact_Level", "PRM")
        self.assertEqual((stage, category), ("bond1", "common"))

    def test_prm_ball_formation_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/EFO_Power", "PRM")
        self.assertEqual((stage, category), ("bond1", "ball_efo"))

    def test_prm_bump_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/Bump_Force_Seg_01", "PRM")
        self.assertEqual((stage, category), ("bump", "force"))

    def test_prm_loop_balance_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/Bal_Loop_Percent", "PRM")
        self.assertEqual((stage, category), ("loop", "balance"))

    def test_prm_bond2_tail_scrub_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/Tail_Scrub_Force", "PRM")
        self.assertEqual((stage, category), ("bond2", "tail_scrub"))

    def test_prm_bits_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/NSOP_Sensitivity", "PRM")
        self.assertEqual((stage, category), ("bits_other", "nsop"))

    def test_prm_quick_adjust_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/Bond_Adjust_Force", "PRM")
        self.assertEqual((stage, category), ("quick_adjust", "bond"))

    def test_phy_mag_handler_keyword_mapping(self) -> None:
        stage, category = ParamClassifier.classify("mag_handler/IN_FIRST_SLOT", "PHY")
        self.assertEqual((stage, category), (None, "slot"))

    def test_phy_workholder_keyword_mapping(self) -> None:
        stage, category = ParamClassifier.classify("workholder/LOT_SEP_MODES", "PHY")
        self.assertEqual((stage, category), (None, "indexing"))

    def test_ref_die_ref_keyword_mapping(self) -> None:
        stage, category = ParamClassifier.classify("die_ref/eyepoint_x_1", "REF")
        self.assertEqual((stage, category), (None, "eyepoint"))

    def test_ref_lead_ref_vll_mapping(self) -> None:
        stage, category = ParamClassifier.classify("lead_ref/corridor_length", "REF")
        self.assertEqual((stage, category), (None, "vll"))

    def test_lf_file_type_remains_unclassified(self) -> None:
        stage, category = ParamClassifier.classify("anything/value", "LF")
        self.assertEqual((stage, category), (None, None))

    def test_unknown_prm_prefix_falls_back_to_unmapped(self) -> None:
        stage, category = ParamClassifier.classify("parms/XYZ_SomeParam", "PRM")
        self.assertEqual((stage, category), ("_unmapped", "xyz"))

    def test_equ_prefix_remains_unmapped(self) -> None:
        stage, category = ParamClassifier.classify("parms/Equ_Factor", "PRM")
        self.assertEqual((stage, category), ("_unmapped", "equ"))

    def test_mag_file_type_remains_unclassified(self) -> None:
        stage, category = ParamClassifier.classify("anything/value", "MAG")
        self.assertEqual((stage, category), (None, None))

    def test_hb_preheat_keyword_mapping(self) -> None:
        stage, category = ParamClassifier.classify("heater/PREHEAT_TEMP", "HB")
        self.assertEqual((stage, category), (None, "preheat"))

    def test_sample_prm_mapping_majority_is_classified(self) -> None:
        repository = self._Repo()
        pipeline = RecipePipeline(repository=repository)
        sample_path = ROOT_DIR / "samples" / "L_WBK_ConnX Elite@PJA3406@ECC17@WAF903898_1"

        with patch("pipeline.extract_metadata", return_value=self._MetadataStub()):
            pipeline.process(sample_path)

        self.assertIsNotNone(repository.saved)
        params = list((repository.saved or {}).get("params", []))  # type: ignore[arg-type]
        prm_rows = [row for row in params if row.get("file_type") == "PRM"]
        self.assertGreater(len(prm_rows), 0)

        mapped_rows = [
            row for row in prm_rows
            if ParamClassifier.classify(str(row.get("param_name") or ""), "PRM")[0] != "_unmapped"
        ]
        self.assertGreaterEqual(len(mapped_rows) / len(prm_rows), 0.8)


if __name__ == "__main__":
    unittest.main()
