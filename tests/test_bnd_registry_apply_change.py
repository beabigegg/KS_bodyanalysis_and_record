from __future__ import annotations

from pathlib import Path
import unittest

from ksbody.pipeline.extractor.decompress import extract_gzip_tar
from ksbody.pipeline.parsers.bnd_registry import BNDRegistryParser

from tests.support import build_sample_recipe_archive


class BNDRegistryApplyChangeTests(unittest.TestCase):
    def _parse_registry(self, variant: str, bnd_name: str):
        root_dir = Path(__file__).resolve().parents[1]
        sample_path = build_sample_recipe_archive(root_dir / ".pytest-samples", variant)
        with extract_gzip_tar(sample_path) as extracted_dir:
            parser = BNDRegistryParser()
            return parser.parse(Path(extracted_dir) / bnd_name, extracted_dir)

    def test_parse_pja3406_roles_and_wire(self) -> None:
        registry = self._parse_registry("pja3406", "MR192600.BND")
        self.assertEqual(registry.mag_handler, "CJ621A20")
        self.assertEqual(registry.workholder, "CJ621A41")
        self.assertEqual(registry.wire_stem, "AP643419")

    def test_parse_pja3406_parms_list_and_bsg_flags(self) -> None:
        registry = self._parse_registry("pja3406", "MR192600.BND")
        self.assertEqual(len(registry.parms_list), 2)
        self.assertTrue(registry.parms_list[0].has_bsg)
        self.assertFalse(registry.parms_list[1].has_bsg)

    def test_parse_ref_type_from_ref_file(self) -> None:
        registry = self._parse_registry("pjs6400", "JA252600.BND")
        ref_types = {entry.stem: entry.ref_type for entry in registry.ref_list}
        self.assertEqual(ref_types.get("AP643419"), "DIE")


if __name__ == "__main__":
    unittest.main()
