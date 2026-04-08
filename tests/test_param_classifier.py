from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from ksbody.pipeline import RecipePipeline
from ksbody.web.utils.param_classifier import ParamClassifier

from tests.support import build_sample_recipe_archive


class ParamClassifierTests(unittest.TestCase):
    class _Repo:
        def __init__(self) -> None:
            self.saved: dict[str, object] | None = None

        def save_recipe(self, **kwargs: object) -> int:
            self.saved = dict(kwargs)
            return 1

    def test_prm_bond1_force_mapping(self) -> None:
        self.assertEqual(ParamClassifier.classify("parms/B1_Force_Seg_01", "PRM"), ("bond1", "force"))

    def test_prm_bond1_common_mapping(self) -> None:
        self.assertEqual(ParamClassifier.classify("parms/B1_Contact_Level", "PRM"), ("bond1", "common"))

    def test_prm_ball_formation_mapping(self) -> None:
        self.assertEqual(ParamClassifier.classify("parms/EFO_Power", "PRM"), ("bond1", "ball_efo"))

    def test_prm_bump_mapping(self) -> None:
        self.assertEqual(ParamClassifier.classify("parms/Bump_Force_Seg_01", "PRM"), ("Bump", "Force"))

    def test_lookup_hit_returns_corrected_bond1_process_step(self) -> None:
        with patch.object(ParamClassifier, "_get_process_step_lookup", return_value={"Bond1_Force_Seg_01": {"process_step": "2. BOND1 相關 / BUMP (First Bond)", "stage": "bond1", "category": "force", "family": None, "feature": None, "description": None, "tunable": True}}):
            semantics = ParamClassifier.classify_semantics("parms/Bond1_Force_Seg_01", "PRM")
        self.assertEqual(semantics.process_step, "2. BOND1 相關 / BUMP (First Bond)")

    def test_lookup_hit_returns_corrected_bump_process_step(self) -> None:
        with patch.object(ParamClassifier, "_get_process_step_lookup", return_value={"Bump_Force_Seg_01": {"process_step": "2. BOND1 相關 / BUMP (First Bond)", "stage": "bump", "category": "force", "family": None, "feature": None, "description": None, "tunable": True}}):
            semantics = ParamClassifier.classify_semantics("parms/Bump_Force_Seg_01", "PRM")
        self.assertEqual(semantics.process_step, "2. BOND1 相關 / BUMP (First Bond)")

    def test_lookup_hit_returns_corrected_bond2_process_step(self) -> None:
        with patch.object(ParamClassifier, "_get_process_step_lookup", return_value={"Bond2_Scrub_Amp": {"process_step": "6. BOND2 相關 (Second Bond / Tail)", "stage": "bond2", "category": "scrub", "family": None, "feature": None, "description": None, "tunable": True}}):
            semantics = ParamClassifier.classify_semantics("parms/Bond2_Scrub_Amp", "PRM")
        self.assertEqual(semantics.process_step, "6. BOND2 相關 (Second Bond / Tail)")

    def test_prm_safety_fence_semantics_mapping(self) -> None:
        semantics = ParamClassifier.classify_semantics("parms/SF10_Pullout_Dist", "PRM")
        self.assertEqual(semantics.stage, "BITS / Other")
        self.assertEqual(semantics.category, "Pullout Dist")
        self.assertEqual(semantics.family, "Safety Fence")
        self.assertEqual(semantics.feature, "Pullout Dist")
        self.assertEqual(semantics.instance, "sf10")
        self.assertTrue(semantics.tunable)

    def test_prm_internal_flag_marked_non_tunable(self) -> None:
        semantics = ParamClassifier.classify_semantics("parms/SomeSetting_Conv", "PRM")
        self.assertEqual(semantics.family, "internal_flag")
        self.assertEqual(semantics.feature, "conversion_flag")
        self.assertFalse(semantics.tunable)

    def test_sample_prm_mapping_majority_is_classified(self) -> None:
        repository = self._Repo()
        pipeline = RecipePipeline(repository=repository)
        root_dir = Path(__file__).resolve().parents[1]
        sample_path = build_sample_recipe_archive(root_dir / ".pytest-samples", "pja3406")
        pipeline.process(sample_path)
        self.assertIsNotNone(repository.saved)
        params = list((repository.saved or {}).get("params", []))
        prm_rows = [row for row in params if row.get("file_type") == "PRM"]
        mapped_rows = [row for row in prm_rows if ParamClassifier.classify(str(row.get("param_name") or ""), "PRM")[0] != "_unmapped"]
        self.assertGreaterEqual(len(mapped_rows) / len(prm_rows), 0.8)


if __name__ == "__main__":
    unittest.main()
