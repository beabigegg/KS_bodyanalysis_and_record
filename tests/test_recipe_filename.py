from __future__ import annotations

from pathlib import Path

import pytest

from ksbody.pipeline.extractor.metadata import MetadataParseError, extract_filename_info
from ksbody.recipe_filename import is_recipe_body_filename, match_recipe_filename


def test_recipe_filename_accepts_standard_and_timestamp_suffix() -> None:
    standard = Path("L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1")
    timestamped = Path("L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1_1775539396")

    assert is_recipe_body_filename(standard) is True
    assert is_recipe_body_filename(timestamped) is True
    assert match_recipe_filename(timestamped) is not None


def test_extract_filename_info_ignores_timestamp_suffix() -> None:
    path = Path("L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1_1775539396")

    assert extract_filename_info(path) == ("PJS6400", "ECC17", "WAF007957", 1)


def test_extract_filename_info_rejects_invalid_suffix() -> None:
    path = Path("L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1_extra")

    with pytest.raises(MetadataParseError):
        extract_filename_info(path)
