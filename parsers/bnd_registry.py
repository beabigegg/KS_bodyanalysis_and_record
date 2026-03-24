from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import logging
import re


@dataclass(frozen=True)
class ParmsEntry:
    stem: str
    has_bsg: bool


@dataclass(frozen=True)
class RefEntry:
    stem: str
    ref_type: str
    name: str | None = None


@dataclass
class ComponentRegistry:
    mag_handler: str | None = None
    workholder: str | None = None
    lead_frame: str | None = None
    magazine: str | None = None
    heat_block: str | None = None
    indexer_ref_system: str | None = None
    wire_stem: str | None = None
    parms_list: list[ParmsEntry] = field(default_factory=list)
    ref_list: list[RefEntry] = field(default_factory=list)
    machine_stem: str | None = None
    product_stem: str | None = None


_SINGLE_ROLE_RE = re.compile(
    r"^(mag_handler|workholder|lead_frame|magazine|heat_block|indexer_ref_system)\s+(\S+)",
    re.IGNORECASE,
)
_PARMS_RE = re.compile(r"^parms\s+(\S+)", re.IGNORECASE)
_REF_RE = re.compile(r"^ref\s+(\S+)", re.IGNORECASE)
_MASTER_WIRE_CHAIN_RE = re.compile(r"^master_wire_chain\s+\d+\s+(\S+)", re.IGNORECASE)


class BNDRegistryParser:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def parse(self, bnd_path: str | Path, extracted_dir: str | Path) -> ComponentRegistry:
        bnd_file = Path(bnd_path)
        root_dir = Path(extracted_dir)
        registry = ComponentRegistry(machine_stem=bnd_file.stem)

        try:
            with bnd_file.open("r", encoding="utf-8", errors="ignore") as stream:
                for raw_line in stream:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue

                    single_role_match = _SINGLE_ROLE_RE.match(line)
                    if single_role_match:
                        role_key = single_role_match.group(1).lower()
                        value_stem = self._stem_from_token(single_role_match.group(2))
                        setattr(registry, role_key, value_stem)
                        continue

                    parms_match = _PARMS_RE.match(line)
                    if parms_match:
                        registry.parms_list.append(
                            ParmsEntry(
                                stem=self._stem_from_token(parms_match.group(1)),
                                has_bsg=bool(re.search(r"\bball\b", line, flags=re.IGNORECASE)),
                            )
                        )
                        continue

                    ref_match = _REF_RE.match(line)
                    if ref_match:
                        ref_stem = self._stem_from_token(ref_match.group(1))
                        ref_type, ref_name = self._read_ref_header(root_dir / f"{ref_stem}.REF")
                        registry.ref_list.append(
                            RefEntry(stem=ref_stem, ref_type=(ref_type or "UNKNOWN"), name=ref_name)
                        )
                        continue

                    wire_match = _MASTER_WIRE_CHAIN_RE.match(line)
                    if wire_match:
                        registry.wire_stem = self._stem_from_token(wire_match.group(1))
        except OSError as exc:
            self.logger.warning("failed to parse BND registry (%s): %s", bnd_file, exc)
            return registry

        self._warn_missing_fields(registry, bnd_file)
        return registry

    def _read_ref_header(self, ref_path: Path) -> tuple[str | None, str | None]:
        ref_type: str | None = None
        ref_name: str | None = None
        try:
            with ref_path.open("r", encoding="utf-8", errors="ignore") as stream:
                for index, raw_line in enumerate(stream):
                    if index >= 20:
                        break
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    key, value = self._extract_kv(line)
                    if key is None:
                        continue
                    normalized = key.lower()
                    if normalized == "ref_type":
                        ref_type = value.upper()
                    elif normalized == "name":
                        ref_name = value
                    if ref_type is not None and ref_name is not None:
                        break
        except OSError as exc:
            self.logger.warning("cannot read REF file (%s): %s", ref_path, exc)
            return "UNKNOWN", None

        if ref_type is None:
            self.logger.warning("missing ref_type in REF file: %s", ref_path)
            ref_type = "UNKNOWN"
        return ref_type, ref_name

    @staticmethod
    def _extract_kv(line: str) -> tuple[str | None, str]:
        if "=" in line:
            left, right = line.split("=", 1)
            key = left.strip()
            if not key:
                return None, ""
            return key, right.strip().strip('"').strip("'")

        tokens = line.split(maxsplit=1)
        if len(tokens) < 2:
            return None, ""
        return tokens[0].strip(), tokens[1].strip().strip('"').strip("'")

    @staticmethod
    def _stem_from_token(token: str) -> str:
        cleaned = token.strip().strip('"').strip("'")
        return Path(cleaned).stem

    def _warn_missing_fields(self, registry: ComponentRegistry, bnd_file: Path) -> None:
        if registry.mag_handler is None:
            self.logger.warning("missing mag_handler in BND: %s", bnd_file)
        if registry.workholder is None:
            self.logger.warning("missing workholder in BND: %s", bnd_file)
        if registry.lead_frame is None:
            self.logger.warning("missing lead_frame in BND: %s", bnd_file)
        if registry.magazine is None:
            self.logger.warning("missing magazine in BND: %s", bnd_file)
        if registry.heat_block is None:
            self.logger.warning("missing heat_block in BND: %s", bnd_file)
        if registry.indexer_ref_system is None:
            self.logger.warning("missing indexer_ref_system in BND: %s", bnd_file)
        if registry.wire_stem is None:
            self.logger.warning("missing master_wire_chain in BND: %s", bnd_file)
