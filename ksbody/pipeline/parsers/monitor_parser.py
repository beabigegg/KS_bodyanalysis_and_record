from __future__ import annotations

from pathlib import Path
import re

from ksbody.pipeline.parsers.base import BaseParser, ParseResult


BLOCK_PATTERN = re.compile(r"^(?P<name>[A-Za-z_][\w-]*)(?:\s+(?P<arg>[^\{]+))?\s*\{$")


class MonitorParser(BaseParser):
    """Parse LHM/VHM files with key-value and loop_id blocks."""

    def parse(self, file_path: str | Path) -> ParseResult:
        path = Path(file_path)
        file_type = path.suffix.lstrip(".").upper()
        result = ParseResult(file_type=file_type)
        stack: list[str] = []

        with path.open("r", encoding="utf-8", errors="ignore") as stream:
            for raw_line in stream:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line == "end":
                    continue

                if line.startswith("}"):
                    if stack:
                        stack.pop()
                    continue

                block_match = BLOCK_PATTERN.match(line)
                if block_match:
                    name = block_match.group("name")
                    arg = (block_match.group("arg") or "").strip()
                    if arg:
                        arg = "_".join(arg.split())
                        stack.append(f"{name}_{arg}")
                    else:
                        stack.append(name)
                    continue

                if "=" not in line:
                    continue

                key, value = [part.strip() for part in line.split("=", 1)]
                param_name = f"{'.'.join(stack)}.{key}" if stack else key
                result.params.append(
                    {
                        "file_type": file_type,
                        "param_name": param_name,
                        "param_value": value,
                        "unit": None,
                        "min_value": None,
                        "max_value": None,
                        "default_value": None,
                    }
                )

        return result
