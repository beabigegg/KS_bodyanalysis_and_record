from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ksbody.recipe_filename import match_recipe_filename


@dataclass(frozen=True)
class RecipeMetadata:
    machine_type: str
    machine_id: str
    product_type: str
    bop: str
    wafer_pn: str
    recipe_version: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class MetadataParseError(ValueError):
    """Raised when metadata cannot be extracted from path/filename."""



def extract_machine_info(source_file: str | Path) -> tuple[str, str]:
    path = Path(source_file)
    parents = path.parents
    if len(parents) < 2:
        raise MetadataParseError(
            f"Path must include machine_type/machine_id folders: {source_file}"
        )

    machine_id = parents[0].name
    machine_type = parents[1].name
    if not machine_type or not machine_id:
        raise MetadataParseError(f"Invalid machine info in path: {source_file}")

    return machine_type, machine_id



def extract_filename_info(source_file: str | Path) -> tuple[str, str, str, int]:
    name = Path(source_file).name
    match = match_recipe_filename(name)
    if not match:
        raise MetadataParseError(f"Filename does not match expected pattern: {name}")

    groups = match.groupdict()
    return (
        groups["product_type"],
        groups["bop"],
        groups["wafer_pn"],
        int(groups["recipe_version"]),
    )



def extract_metadata(source_file: str | Path) -> RecipeMetadata:
    machine_type, machine_id = extract_machine_info(source_file)
    product_type, bop, wafer_pn, recipe_version = extract_filename_info(source_file)
    return RecipeMetadata(
        machine_type=machine_type,
        machine_id=machine_id,
        product_type=product_type,
        bop=bop,
        wafer_pn=wafer_pn,
        recipe_version=recipe_version,
    )



def extract_bnd_metadata(parsed_rows: list[dict[str, object]]) -> dict[str, object]:
    lookup = {
        row["param_name"]: row.get("param_value")
        for row in parsed_rows
        if "param_name" in row
    }
    date_time_raw = lookup.get("date_time")
    return {
        "recipe_name": lookup.get("name"),
        "mc_serial": lookup.get("mc_serial_number"),
        "sw_version": lookup.get("mc_software_version"),
        "recipe_datetime": _parse_datetime(date_time_raw),
        "lot_id": None,
    }



def _parse_datetime(value: object) -> object:
    if not isinstance(value, str):
        return None

    for fmt in ("%m/%d/%y %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            from datetime import datetime

            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None
