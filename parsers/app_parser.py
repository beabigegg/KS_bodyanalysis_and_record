from __future__ import annotations

from pathlib import Path

from parsers.base import BaseParser, ParseResult


APP_FIELD_MAPPING = {
    "CapManufacturer": "cap_manufacturer",
    "CapPartNumber": "cap_part_number",
    "TipDia": "cap_tip_dia",
    "HoleDiameter": "cap_hole_dia",
    "ChamferDia": "chamfer_dia",
    "InnerConeAngle": "inner_cone_angle",
    "FaceAngle": "face_angle",
    "WireManufacturer": "wire_manufacturer",
    "WirePartNumber": "wire_part_number",
    "WireDia": "wire_dia",
    "WireMetal": "wire_metal",
}


class AppParser(BaseParser):
    def parse(self, file_path: str | Path) -> ParseResult:
        path = Path(file_path)
        file_type = path.suffix.lstrip(".").upper()
        raw_values: dict[str, str] = {}
        block_key: str | None = None
        block_lines: list[str] = []

        with path.open("r", encoding="utf-8", errors="ignore") as stream:
            for raw_line in stream:
                line = raw_line.rstrip("\n")
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                if stripped == "end":
                    continue

                if block_key is not None:
                    if stripped == "}":
                        raw_values[block_key] = "\n".join(block_lines).strip()
                        block_key = None
                        block_lines = []
                    else:
                        block_lines.append(stripped)
                    continue

                if "=" not in stripped:
                    continue

                key, value = stripped.split("=", 1)
                key = key.strip()
                value = value.strip()

                if value == "{":
                    block_key = key
                    block_lines = []
                    continue

                raw_values[key] = value

        app_spec = {
            target: raw_values.get(source)
            for source, target in APP_FIELD_MAPPING.items()
        }

        return ParseResult(file_type=file_type, app_spec=app_spec)
