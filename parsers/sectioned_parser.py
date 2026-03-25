from __future__ import annotations

from pathlib import Path
import re

from parsers.base import BaseParser, ParseResult

# WIR group declaration: group <stem.PRM> <wir_group_no> [other args...]
_WIR_GROUP_RE = re.compile(r"^group\s+\S+\.PRM\s+\d+", re.IGNORECASE)

# Block headers that contain binary data — skip until matching closing brace
_BINARY_BLOCK_RE = re.compile(r"^data\s+\d+\s*\{$", re.IGNORECASE)


class SectionedParser(BaseParser):
    """Parse section/block files with nested braces."""

    def parse(self, file_path: str | Path) -> ParseResult:
        path = Path(file_path)
        file_type = path.suffix.lstrip(".").upper()
        result = ParseResult(file_type=file_type)
        context_stack: list[str] = []
        skip_depth = 0  # > 0 means inside a binary data block

        with path.open("r", encoding="utf-8", errors="ignore") as stream:
            for raw_line in stream:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line == "end":
                    continue

                # When inside a binary block, only track braces for depth
                if skip_depth > 0:
                    skip_depth += line.count("{") - line.count("}")
                    continue

                if line.startswith("}"):
                    if context_stack:
                        context_stack.pop()
                    continue

                if line.endswith("{"):
                    # Detect binary data blocks like "data 6196 {"
                    if _BINARY_BLOCK_RE.match(line):
                        skip_depth = 1
                        continue
                    context_stack.append(self._normalize_block_header(line[:-1].strip()))
                    continue

                # Skip lines with non-printable characters (binary residue)
                if not line.replace("\t", " ").isprintable():
                    continue

                if file_type == "WIR" and line.startswith("connect"):
                    self._parse_connect_line(line, context_stack, result, file_type)
                    continue

                if file_type == "WIR" and _WIR_GROUP_RE.match(line):
                    self._parse_wir_group_line(line, context_stack, result, file_type)
                    continue

                entry = self._parse_key_value(line)
                if entry is None:
                    continue

                full_name = self._join_name(context_stack, entry["key"])
                param = {
                    "file_type": file_type,
                    "param_name": full_name,
                    "param_value": entry["value"],
                    "unit": entry.get("unit"),
                    "min_value": None,
                    "max_value": None,
                    "default_value": None,
                }
                result.params.append(param)

                if file_type == "BSG":
                    bsg_row = self._to_bsg_row(full_name, entry["value"])
                    if bsg_row:
                        result.bsg_rows.append(bsg_row)

        return result

    @staticmethod
    def _normalize_block_header(header: str) -> str:
        tokens = header.split()
        if not tokens:
            return "section"
        if len(tokens) >= 2 and tokens[1].isdigit():
            return f"{tokens[0]}_{tokens[1]}"
        return "_".join(tokens)

    @staticmethod
    def _parse_key_value(line: str) -> dict[str, str] | None:
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                return None
            # Extract trailing alphabetic unit token (e.g. "mils", "deg")
            # when the preceding tokens are all numeric.
            unit: str | None = None
            tokens = value.split()
            if (
                len(tokens) >= 2
                and re.fullmatch(r"[a-zA-Z]+", tokens[-1])
                and all(
                    re.fullmatch(r"[+-]?\d+(\.\d+)?([eE][+-]?\d+)?", t)
                    for t in tokens[:-1]
                )
            ):
                unit = tokens[-1]
                value = " ".join(tokens[:-1])
            return {"key": key, "value": value, "unit": unit}

        # Handle inline brace expressions like: pbi_selected { 1-5 }
        m = re.match(r"^(\S+)\s+\{(.+)\}\s*$", line)
        if m:
            return {"key": m.group(1), "value": m.group(2).strip()}

        # Handle tabular lines like: mc_serial_number 10354 10626
        tokens = line.split()
        if len(tokens) < 2:
            return None

        key = tokens[0]
        value = tokens[-1]
        if (
            len(tokens) >= 3
            and re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}", tokens[-2])
            and re.fullmatch(r"\d{2}:\d{2}:\d{2}", tokens[-1])
        ):
            value = f"{tokens[-2]} {tokens[-1]}"
        return {"key": key, "value": value}

    @staticmethod
    def _join_name(context_stack: list[str], key: str) -> str:
        if not context_stack:
            return key
        return f"{'.'.join(context_stack)}.{key}"

    def _parse_connect_line(
        self,
        line: str,
        context_stack: list[str],
        result: ParseResult,
        file_type: str,
    ) -> None:
        tokens = line.split()
        # connect <id> <instance> <site> <group> <profile>
        if len(tokens) < 3:
            return

        connect_id = tokens[1]
        base = self._join_name(context_stack, f"connect_{connect_id}")

        fields = {
            "id": connect_id,
            "instance": tokens[2] if len(tokens) > 2 else None,
            "site": tokens[3] if len(tokens) > 3 else None,
            "group": tokens[4] if len(tokens) > 4 else None,
            "profile": tokens[5] if len(tokens) > 5 else None,
        }

        for field, value in fields.items():
            if value is None:
                continue
            result.params.append(
                {
                    "file_type": file_type,
                    "param_name": f"{base}.{field}",
                    "param_value": value,
                    "unit": None,
                    "min_value": None,
                    "max_value": None,
                    "default_value": None,
                }
            )

    @staticmethod
    def _parse_wir_group_line(
        line: str,
        context_stack: list[str],
        result: ParseResult,
        file_type: str,
    ) -> None:
        """Parse WIR group declaration: group <stem.PRM> <wir_group_no> [args...]

        Stores as param: group_<STEM>.wir_group_no = <wir_group_no>
        Example: "group CJ621A20.PRM 2 1 3 2 3 2" → "group_CJ621A20.wir_group_no" = "2"
        """
        tokens = line.split()
        if len(tokens) < 3:
            return
        stem = Path(tokens[1]).stem          # "CJ621A20"
        wir_group_no = tokens[2]             # "2"
        base = SectionedParser._join_name(context_stack, f"group_{stem}")
        result.params.append(
            {
                "file_type": file_type,
                "param_name": f"{base}.wir_group_no",
                "param_value": wir_group_no,
                "unit": None,
                "min_value": None,
                "max_value": None,
                "default_value": None,
            }
        )

    @staticmethod
    def _to_bsg_row(param_name: str, value: str) -> dict[str, str] | None:
        segments = param_name.split(".")
        ball_group_segment = next((s for s in segments if s.startswith("ball_group_")), None)
        if not ball_group_segment:
            return None

        ball_group = ball_group_segment.split("_", 2)[-1]
        inspection_key = segments[-1]
        process_key = ".".join(segments[1:-1]) if len(segments) > 2 else None

        return {
            "ball_group": ball_group,
            "inspection_key": inspection_key,
            "process_key": process_key,
            "value": value,
        }
