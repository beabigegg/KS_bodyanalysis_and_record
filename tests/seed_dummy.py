"""Seed dummy import records for testing Cross-Machine Compare.

Imports the sample recipe files as multiple machines so the compare
page has real data with proper machine_id values from folder structure.

Usage:
    python tests/seed_dummy.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from db.repository import RecipeRepository
from pipeline import RecipePipeline
from sqlalchemy import create_engine

ROOT_DIR = Path(__file__).resolve().parents[1]
SAMPLES_DIR = ROOT_DIR / "samples"
TEMP_DIR = ROOT_DIR / "temp_seed"

MACHINE_TYPE = "ConnX Elite"

# (machine_id, sample_name) — 同一 product/bop/wafer 才能在 compare 中對比
MACHINES = [
    ("GWBK-0001", "L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1"),
    ("GWBK-0002", "L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1"),
    ("GWBK-0003", "L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1"),
    ("GWBK-0004", "L_WBK_ConnX Elite@PJA3406@ECC17@WAF903898_1"),
    ("GWBK-0005", "L_WBK_ConnX Elite@PJA3406@ECC17@WAF903898_1"),
]


def main() -> None:
    settings = load_settings(str(ROOT_DIR / "config.yaml"))
    engine = create_engine(settings.mysql.sqlalchemy_url())
    repo = RecipeRepository(engine)
    pipeline = RecipePipeline(repository=repo)

    results: list[str] = []

    for machine_id, sample_name in MACHINES:
        src = SAMPLES_DIR / sample_name
        if not src.exists():
            print(f"[SKIP] sample not found: {src}")
            continue

        stage_dir = TEMP_DIR / MACHINE_TYPE / machine_id
        stage_dir.mkdir(parents=True, exist_ok=True)
        staged = stage_dir / sample_name
        shutil.copy2(src, staged)

        try:
            r = pipeline.process(staged)
            results.append(
                f"  [{machine_id}] import_id={r.recipe_import_id} "
                f"params={r.parameter_count} bsg={r.bsg_count}"
            )
        except Exception as exc:  # noqa: BLE001
            results.append(f"  [{machine_id}] FAILED: {exc}")

    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    print("Seed complete:")
    for line in results:
        print(line)


if __name__ == "__main__":
    main()
