from __future__ import annotations

from pathlib import Path

from parsers.base import BaseParser, ParseResult


class KeyValueParser(BaseParser):
    """Parse PHY/PRM/LF/MAG key-value and table-like parameter lines."""

    def parse(self, file_path: str | Path) -> ParseResult:
        path = Path(file_path)
        file_type = path.suffix.lstrip(".").upper()
        result = ParseResult(file_type=file_type)

        with path.open("r", encoding="utf-8", errors="ignore") as stream:
            for raw_line in stream:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                parsed = self._parse_line(line)
                if parsed is None:
                    continue

                result.params.append(
                    {
                        "file_type": file_type,
                        "param_name": parsed["param_name"],
                        "param_value": parsed.get("param_value"),
                        "unit": parsed.get("unit"),
                        "min_value": parsed.get("min_value"),
                        "max_value": parsed.get("max_value"),
                        "default_value": parsed.get("default_value"),
                    }
                )

        return result

    def _parse_line(self, line: str) -> dict[str, str | None] | None:
        if "=" in line:
            left, right = line.split("=", 1)
            key = left.strip()
            right_tokens = right.split()
            if not key:
                return None
            if not right_tokens:
                return {
                    "param_name": key,
                    "param_value": "",
                    "unit": None,
                    "min_value": None,
                    "max_value": None,
                    "default_value": None,
                }

            # Format: value units sys_type parm_type class min max [default prc_min prc_max]
            #         [0]   [1]   [2]      [3]       [4]  [5] [6]  [7]     [8]      [9]
            if len(right_tokens) >= 7:
                return {
                    "param_name": key,
                    "param_value": self._clean(right_tokens[0]),
                    "unit": self._clean(right_tokens[1]),
                    "min_value": self._clean(right_tokens[5]),
                    "max_value": self._clean(right_tokens[6]),
                    "default_value": self._clean(right_tokens[7]) if len(right_tokens) > 7 else None,
                }

            return {
                "param_name": key,
                "param_value": self._clean(" ".join(right_tokens)),
                "unit": None,
                "min_value": None,
                "max_value": None,
                "default_value": None,
            }

        # Handle simple tab/space delimited key-value lines.
        tokens = line.split()
        if len(tokens) < 2:
            return None

        return {
            "param_name": tokens[0],
            "param_value": self._clean(" ".join(tokens[1:])),
            "unit": None,
            "min_value": None,
            "max_value": None,
            "default_value": None,
        }

    @staticmethod
    def _clean(value: str) -> str:
        return value.strip().strip('"')
