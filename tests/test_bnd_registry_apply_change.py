from __future__ import annotations

from pathlib import Path
import unittest

from extractor.decompress import extract_gzip_tar
from parsers.bnd_registry import BNDRegistryParser


ROOT_DIR = Path(__file__).resolve().parents[1]
SAMPLES_DIR = ROOT_DIR / "samples"


class BNDRegistryApplyChangeTests(unittest.TestCase):
    def _parse_registry(self, sample_name: str, bnd_name: str):
        sample_path = SAMPLES_DIR / sample_name
        with extract_gzip_tar(sample_path) as extracted_dir:
            parser = BNDRegistryParser()
            return parser.parse(Path(extracted_dir) / bnd_name, extracted_dir)

    def test_parse_pja3406_roles_and_wire(self) -> None:
        registry = self._parse_registry(
            "L_WBK_ConnX Elite@PJA3406@ECC17@WAF903898_1",
            "MR192600.BND",
        )
        self.assertEqual(registry.mag_handler, "CJ621A20")
        self.assertEqual(registry.workholder, "CJ621A41")
        self.assertEqual(registry.wire_stem, "CJ621A20")

    def test_parse_pja3406_parms_list_and_bsg_flags(self) -> None:
        registry = self._parse_registry(
            "L_WBK_ConnX Elite@PJA3406@ECC17@WAF903898_1",
            "MR192600.BND",
        )
        self.assertEqual(len(registry.parms_list), 2)
        self.assertTrue(registry.parms_list[0].has_bsg)
        self.assertFalse(registry.parms_list[1].has_bsg)

    def test_parse_ref_type_from_ref_file(self) -> None:
        registry = self._parse_registry(
            "L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1",
            "JA252600.BND",
        )
        ref_types = {entry.stem: entry.ref_type for entry in registry.ref_list}
        self.assertEqual(ref_types.get("AP643419"), "DIE")


if __name__ == "__main__":
    unittest.main()
