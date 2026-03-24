from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT_DIR / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.param_classifier import ParamClassifier  # noqa: E402


class ParamClassifierTests(unittest.TestCase):
    def test_prm_bond1_segment_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/B1_Force_Seg_01", "PRM")
        self.assertEqual((stage, category), ("bond1", "seg_01"))

    def test_prm_bond1_without_segment_falls_back_to_misc(self) -> None:
        stage, category = ParamClassifier.classify("parms/B1_Contact_Level", "PRM")
        self.assertEqual((stage, category), ("bond1", "misc"))

    def test_prm_ball_formation_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/EFO_Power", "PRM")
        self.assertEqual((stage, category), ("ball_formation", "efo"))

    def test_prm_loop_balance_mapping(self) -> None:
        stage, category = ParamClassifier.classify("parms/Bal_Loop_Percent", "PRM")
        self.assertEqual((stage, category), ("loop", "balance"))

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

    def test_equ_prefix_uses_equalization_category(self) -> None:
        stage, category = ParamClassifier.classify("parms/Equ_Factor", "PRM")
        self.assertEqual((stage, category), ("_unmapped", "equalization"))

    def test_mag_file_type_remains_unclassified(self) -> None:
        stage, category = ParamClassifier.classify("anything/value", "MAG")
        self.assertEqual((stage, category), (None, None))

    def test_hb_preheat_keyword_mapping(self) -> None:
        stage, category = ParamClassifier.classify("heater/PREHEAT_TEMP", "HB")
        self.assertEqual((stage, category), (None, "preheat"))


if __name__ == "__main__":
    unittest.main()
