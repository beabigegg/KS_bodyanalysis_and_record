from __future__ import annotations

from pathlib import Path
import unittest

from ksbody.pipeline import RecipePipeline, resolve_role, should_keep_parms_2
from ksbody.pipeline.parsers.bnd_registry import ComponentRegistry, ParmsEntry, RefEntry

from tests.support import build_sample_recipe_archive


class _FakeRepository:
    def __init__(self) -> None:
        self.saved: dict[str, object] | None = None

    def save_recipe(self, **kwargs: object) -> int:
        self.saved = dict(kwargs)
        return 123


class PipelineApplyChangeTests(unittest.TestCase):
    def _run_pipeline(self, variant: str) -> list[dict[str, object]]:
        repository = _FakeRepository()
        pipeline = RecipePipeline(repository=repository)
        root_dir = Path(__file__).resolve().parents[1]
        sample_path = build_sample_recipe_archive(root_dir / ".pytest-samples", variant)
        pipeline.process(sample_path)
        self.assertIsNotNone(repository.saved)
        return list((repository.saved or {}).get("params", []))

    def test_resolve_role_for_phy_and_prm(self) -> None:
        registry = ComponentRegistry(
            mag_handler="CJ621A20",
            workholder="CJ621A41",
            parms_list=[ParmsEntry(stem="CJ621A20", has_bsg=True), ParmsEntry(stem="CJ621A41", has_bsg=False)],
            ref_list=[RefEntry(stem="CJ621A20", ref_type="LEAD"), RefEntry(stem="CJ621A41", ref_type="DIE")],
        )
        self.assertEqual(resolve_role("CJ621A20", "PHY", registry), "mag_handler")
        self.assertEqual(resolve_role("CJ621A41", "PHY", registry), "workholder")
        self.assertEqual(resolve_role("CJ621A20", "PRM", registry), "parms")
        self.assertIsNone(resolve_role("CJ621A20", "LF", registry))

    def test_resolve_role_for_wir(self) -> None:
        registry = ComponentRegistry(wire_stem="AP643419")
        self.assertEqual(resolve_role("AP643419", "WIR", registry), "wire")
        self.assertIsNone(resolve_role("OTHER123", "WIR", registry))
        self.assertIsNone(resolve_role("AP643419", "WIR", ComponentRegistry()))

    def test_should_keep_parms_2(self) -> None:
        p1 = ParmsEntry(stem="A", has_bsg=True)
        p2 = ParmsEntry(stem="B", has_bsg=False)
        parsed_params = {"A": [{"param_name": "Bond1_Force_Seg_01", "param_value": "150"}], "B": [{"param_name": "Bond1_Force_Seg_01", "param_value": "150"}]}
        self.assertTrue(should_keep_parms_2(p1, p2, parsed_params))
        self.assertFalse(should_keep_parms_2(p1, ParmsEntry(stem="B", has_bsg=True), parsed_params))

    def test_pipeline_outputs_semantic_prefixes_for_pja3406(self) -> None:
        names = {str(row.get("param_name")) for row in self._run_pipeline("pja3406")}
        self.assertIn("mag_handler/IN_FIRST_SLOT", names)
        self.assertIn("die_ref/num_sites", names)
        self.assertIn("lead_ref/num_sites", names)
        self.assertIn("parms_2/Bond1_Force_Seg_01", names)
        self.assertNotIn("CJ621A20/IN_FIRST_SLOT", names)

    def test_pipeline_keeps_single_parms_for_pjs6400(self) -> None:
        names = {str(row.get("param_name")) for row in self._run_pipeline("pjs6400")}
        self.assertIn("parms/Bond1_Force_Seg_01", names)
        self.assertNotIn("parms_2/Bond1_Force_Seg_01", names)


if __name__ == "__main__":
    unittest.main()
