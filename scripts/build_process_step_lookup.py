"""Convert K&S_Recipe_Organized_by_Process.csv to process_step_lookup.json.

Usage:
    python scripts/build_process_step_lookup.py

Reads:  K&S_Recipe_Organized_by_Process.csv  (repo root)
Writes: web/config/process_step_lookup.json
"""
from __future__ import annotations

import csv
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "K&S_Recipe_Organized_by_Process.csv"
OUTPUT_PATH = REPO_ROOT / "web" / "config" / "process_step_lookup.json"

KEEP_FIELDS = ("process_step", "stage", "category", "family", "feature", "description", "tunable")
SYSTEM_MONITORING_STEP = "7. 系統/監控/其他 (System & Monitoring)"
BOND1_STEP = "2. BOND1 相關 / BUMP (First Bond)"
BOND2_STEP = "6. BOND2 相關 (Second Bond / Tail)"


def _correct_process_step_for_bond_prefix(param_name: str, process_step: str | None) -> str | None:
    if process_step != SYSTEM_MONITORING_STEP:
        return process_step

    prefix = (param_name.split("_", 1)[0] or "").strip().upper()
    if prefix in {"BOND1", "BUMP"}:
        return BOND1_STEP
    if prefix == "BOND2":
        return BOND2_STEP
    return process_step


def _parse_tunable(value: str) -> bool | None:
    if not value:
        return None
    return value.strip().lower() not in {"false", "0", "no", ""}


def build_lookup(csv_path: Path) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    with csv_path.open(encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            param_name = (row.get("param_name") or "").strip()
            if not param_name:
                continue
            process_step = (row.get("process_step_logic") or "").strip() or None
            process_step = _correct_process_step_for_bond_prefix(param_name, process_step)
            stage = (row.get("stage") or "").strip() or None
            category = (row.get("category") or "").strip() or None
            family = (row.get("family") or "").strip() or None
            feature = (row.get("feature") or "").strip() or None
            description = (row.get("description") or "").strip() or None
            tunable_raw = (row.get("tunable") or "").strip()
            tunable: bool | None = None
            if tunable_raw:
                tunable = tunable_raw.lower() not in {"false", "0", "no"}

            if param_name in lookup:
                log.warning("Duplicate param_name '%s' — keeping first occurrence", param_name)
                continue

            lookup[param_name] = {
                "process_step": process_step,
                "stage": stage,
                "category": category,
                "family": family,
                "feature": feature,
                "description": description,
                "tunable": tunable,
            }
    return lookup


def main() -> None:
    if not CSV_PATH.exists():
        log.error("CSV not found: %s", CSV_PATH)
        sys.exit(1)

    lookup = build_lookup(CSV_PATH)
    log.info("Built lookup with %d entries", len(lookup))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(lookup, fh, ensure_ascii=False, indent=2)
    log.info("Written to %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
