from __future__ import annotations

from pathlib import Path
import re

RECIPE_FILENAME_PATTERN = re.compile(
    r"^L_[^@]+@(?P<product_type>[^@]+)@(?P<bop>[^@]+)@(?P<wafer_pn>[^_]+)_(?P<recipe_version>\d+)(?:_(?P<timestamp>\d+))?$"
)


def match_recipe_filename(path: str | Path) -> re.Match[str] | None:
    return RECIPE_FILENAME_PATTERN.match(Path(path).name)


def is_recipe_body_filename(path: str | Path) -> bool:
    return match_recipe_filename(path) is not None
