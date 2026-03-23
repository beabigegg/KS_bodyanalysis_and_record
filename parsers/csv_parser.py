from __future__ import annotations

import csv
from pathlib import Path

from parsers.base import BaseParser, ParseResult


class CsvParser(BaseParser):
    """Parse AID measurement-definition files."""

    def parse(self, file_path: str | Path) -> ParseResult:
        path = Path(file_path)
        file_type = path.suffix.lstrip(".").upper()
        result = ParseResult(file_type=file_type)

        with path.open("r", encoding="utf-8", errors="ignore", newline="") as stream:
            reader = csv.reader(stream)
            for row in reader:
                if not row:
                    continue
                measurement_name = row[0].strip()
                if not measurement_name:
                    continue
                unit = row[1].strip() if len(row) > 1 and row[1].strip() else None

                result.params.append(
                    {
                        "file_type": file_type,
                        "param_name": measurement_name,
                        "param_value": unit,
                        "unit": unit,
                        "min_value": None,
                        "max_value": None,
                        "default_value": None,
                    }
                )

        return result
