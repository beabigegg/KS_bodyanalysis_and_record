from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from parsers.bnd_registry import ComponentRegistry, ParmsEntry, RefEntry
from pipeline import RecipePipeline, resolve_role, should_keep_parms_2


ROOT_DIR = Path(__file__).resolve().parents[1]
SAMPLES_DIR = ROOT_DIR / "samples"


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


class _FakeRepository:
    def __init__(self) -> None:
        self.saved: dict[str, object] | None = None

    def save_recipe(self, **kwargs: object) -> int:
        self.saved = dict(kwargs)
        return 123


class PipelineApplyChangeTests(unittest.TestCase):
    def _run_pipeline(self, sample_name: str) -> list[dict[str, object]]:
        repository = _FakeRepository()
        pipeline = RecipePipeline(repository=repository)
        sample_path = SAMPLES_DIR / sample_name

        with patch("pipeline.extract_metadata", return_value=_MetadataStub()):
            pipeline.process(sample_path)

        self.assertIsNotNone(repository.saved)
        saved = repository.saved or {}
        return list(saved.get("params", []))  # type: ignore[return-value]

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
        parsed_params = {
            "A": [{"param_name": "Bond1_Force_Seg_01", "param_value": "150"}],
            "B": [{"param_name": "Bond1_Force_Seg_01", "param_value": "150"}],
        }

        self.assertTrue(should_keep_parms_2(p1, p2, parsed_params))

        p2_same_bsg = ParmsEntry(stem="B", has_bsg=True)
        self.assertFalse(should_keep_parms_2(p1, p2_same_bsg, parsed_params))

    def test_pipeline_outputs_semantic_prefixes_for_pja3406(self) -> None:
        params = self._run_pipeline("L_WBK_ConnX Elite@PJA3406@ECC17@WAF903898_1")
        names = {str(row.get("param_name")) for row in params}

        self.assertIn("mag_handler/IN_FIRST_SLOT", names)
        self.assertIn("die_ref/num_sites", names)
        self.assertIn("lead_ref/num_sites", names)
        self.assertIn("parms_2/Bond1_Force_Seg_01", names)
        self.assertNotIn("CJ621A20/IN_FIRST_SLOT", names)

    def test_pipeline_keeps_single_parms_for_pjs6400(self) -> None:
        params = self._run_pipeline("L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1")
        names = {str(row.get("param_name")) for row in params}

        self.assertIn("parms/Bond1_Force_Seg_01", names)
        self.assertNotIn("parms_2/Bond1_Force_Seg_01", names)


if __name__ == "__main__":
    unittest.main()
