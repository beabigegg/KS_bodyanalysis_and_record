from __future__ import annotations

import tempfile
from pathlib import Path
import sys
import textwrap
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.build_process_step_lookup import (  # noqa: E402
    BOND1_STEP,
    BOND2_STEP,
    SYSTEM_MONITORING_STEP,
    build_lookup,
)


class BuildProcessStepLookupTests(unittest.TestCase):
    def test_bond_prefixed_rows_are_remapped_from_system_monitoring(self) -> None:
        csv_payload = textwrap.dedent(
            f"""\
            param_name,process_step_logic,stage,category,family,feature,description,tunable
            Bond1_Force_Seg_01,{SYSTEM_MONITORING_STEP},Bond1,force,,,Bond1 force,true
            Bump_Force_Seg_01,{SYSTEM_MONITORING_STEP},Bump,force,,,Bump force,true
            Bond2_Scrub_Amp,{SYSTEM_MONITORING_STEP},Bond2,scrub,,,Bond2 scrub,true
            Bond2_Custom,5. Looping (Looping),Bond2,misc,,,Already specific,false
            """
        )
        with tempfile.TemporaryDirectory(dir=ROOT_DIR) as temp_dir:
            csv_path = Path(temp_dir) / "lookup.csv"
            csv_path.write_text(csv_payload, encoding="utf-8")

            lookup = build_lookup(csv_path)

        self.assertEqual(lookup["Bond1_Force_Seg_01"]["process_step"], BOND1_STEP)
        self.assertEqual(lookup["Bump_Force_Seg_01"]["process_step"], BOND1_STEP)
        self.assertEqual(lookup["Bond2_Scrub_Amp"]["process_step"], BOND2_STEP)
        self.assertEqual(lookup["Bond2_Custom"]["process_step"], "5. Looping (Looping)")
        self.assertNotEqual(lookup["Bond1_Force_Seg_01"]["process_step"], SYSTEM_MONITORING_STEP)
        self.assertNotEqual(lookup["Bump_Force_Seg_01"]["process_step"], SYSTEM_MONITORING_STEP)
        self.assertNotEqual(lookup["Bond2_Scrub_Amp"]["process_step"], SYSTEM_MONITORING_STEP)


if __name__ == "__main__":
    unittest.main()
