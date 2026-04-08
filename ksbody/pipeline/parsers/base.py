from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParseResult:
    file_type: str
    params: list[dict[str, object]] = field(default_factory=list)
    app_spec: dict[str, object] | None = None
    bsg_rows: list[dict[str, object]] = field(default_factory=list)
    rpm_limits: list[dict[str, object]] = field(default_factory=list)
    rpm_reference: list[dict[str, object]] = field(default_factory=list)

    def extend(self, other: "ParseResult") -> None:
        self.params.extend(other.params)
        self.bsg_rows.extend(other.bsg_rows)
        self.rpm_limits.extend(other.rpm_limits)
        self.rpm_reference.extend(other.rpm_reference)
        if other.app_spec:
            self.app_spec = other.app_spec


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str | Path) -> ParseResult:
        raise NotImplementedError
