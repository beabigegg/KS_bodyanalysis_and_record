from __future__ import annotations

from pathlib import Path

from parsers.app_parser import AppParser
from parsers.base import BaseParser
from parsers.csv_parser import CsvParser
from parsers.key_value_parser import KeyValueParser
from parsers.monitor_parser import MonitorParser
from parsers.sectioned_parser import SectionedParser
from parsers.sqlite_parser import SqliteParser


class ParserRegistry:
    def __init__(self) -> None:
        key_value = KeyValueParser()
        sectioned = SectionedParser()
        monitor = MonitorParser()

        self._parsers: dict[str, BaseParser] = {
            "PHY": key_value,
            "PRM": key_value,
            "LF": key_value,
            "MAG": key_value,
            "PPC": key_value,
            "BND": sectioned,
            "REF": sectioned,
            "HB": sectioned,
            "WIR": sectioned,
            "BSG": sectioned,
            "AIC": sectioned,
            "APP": AppParser(),
            "AID": CsvParser(),
            "RPM": SqliteParser(),
            "LHM": monitor,
            "VHM": monitor,
        }

    def get_parser(self, extension: str) -> BaseParser | None:
        return self._parsers.get(extension.upper())

    def parser_for_file(self, file_path: str | Path) -> BaseParser | None:
        ext = Path(file_path).suffix.lstrip(".").upper()
        if not ext:
            return None
        return self.get_parser(ext)
