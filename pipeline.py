from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging

from db.repository import RecipeRepository
from extractor.decompress import extract_gzip_tar
from extractor.metadata import extract_bnd_metadata, extract_metadata
from parsers.bnd_registry import BNDRegistryParser, ComponentRegistry, ParmsEntry
from parsers.registry import ParserRegistry

ROLE_REQUIRED_FILE_TYPES = {"PHY", "PRM", "REF", "WIR"}


@dataclass
class PipelineResult:
    source_file: Path
    recipe_import_id: int | None
    total_files: int
    parsed_files: int
    skipped_files: int
    failed_files: int
    parameter_count: int
    bsg_count: int
    rpm_limits_count: int
    rpm_reference_count: int


@dataclass
class _PendingPrm:
    stem: str
    file_path: Path
    params: list[dict[str, object]]
    role: str | None
    fallback_prefix: str | None


def resolve_role(stem: str, file_type: str, registry: ComponentRegistry | None) -> str | None:
    if registry is None:
        return None

    normalized_type = file_type.upper()
    if normalized_type == "PHY":
        if stem == registry.mag_handler:
            return "mag_handler"
        if stem == registry.workholder:
            return "workholder"
        return None

    if normalized_type == "PRM":
        for index, entry in enumerate(registry.parms_list, start=1):
            if stem == entry.stem:
                return "parms" if index == 1 else f"parms_{index}"
        return None

    if normalized_type == "REF":
        for index, entry in enumerate(registry.ref_list, start=1):
            if stem != entry.stem:
                continue
            ref_type = (entry.ref_type or "").upper()
            if ref_type == "DIE":
                return "die_ref"
            if ref_type == "LEAD":
                return "lead_ref"
            return f"ref_{index}"
        return None

    if normalized_type == "WIR":
        if registry.wire_stem and stem == registry.wire_stem:
            return "wire"
        return None

    return None


def should_keep_parms_2(
    p1: ParmsEntry,
    p2: ParmsEntry,
    parsed_params: dict[str, list[dict[str, object]]],
) -> bool:
    if p1.has_bsg != p2.has_bsg:
        return True
    values_1 = _params_to_value_map(parsed_params.get(p1.stem, []))
    values_2 = _params_to_value_map(parsed_params.get(p2.stem, []))
    return values_1 != values_2


def _prefix_params(rows: list[dict[str, object]], prefix: str) -> list[dict[str, object]]:
    prefixed_rows: list[dict[str, object]] = []
    for row in rows:
        param_name = str(row.get("param_name") or "")
        if param_name.startswith(f"{prefix}/"):
            prefixed_name = param_name
        else:
            prefixed_name = f"{prefix}/{param_name}"
        prefixed_rows.append({**row, "param_name": prefixed_name})
    return prefixed_rows


def _params_to_value_map(rows: list[dict[str, object]]) -> dict[str, object]:
    return {str(row.get("param_name") or ""): row.get("param_value") for row in rows}


def _ordered_prms(
    pending_prms: list[_PendingPrm],
    registry: ComponentRegistry | None,
) -> list[_PendingPrm]:
    if not pending_prms:
        return []
    if registry is None or not registry.parms_list:
        return sorted(pending_prms, key=lambda item: str(item.file_path))

    by_stem: dict[str, _PendingPrm] = {item.stem: item for item in pending_prms}
    ordered: list[_PendingPrm] = []
    used_stems: set[str] = set()

    for entry in registry.parms_list:
        item = by_stem.get(entry.stem)
        if item is None:
            continue
        ordered.append(item)
        used_stems.add(item.stem)

    for item in sorted(pending_prms, key=lambda it: str(it.file_path)):
        if item.stem in used_stems:
            continue
        ordered.append(item)
    return ordered


class RecipePipeline:
    def __init__(
        self,
        repository: RecipeRepository | None,
        registry: ParserRegistry | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.repository = repository
        self.registry = registry or ParserRegistry()
        self.logger = logger or logging.getLogger(__name__)

    def process(self, source_file: str | Path) -> PipelineResult:
        source = Path(source_file)
        metadata = extract_metadata(source)

        import_record: dict[str, object] = {
            **metadata.to_dict(),
            "recipe_name": None,
            "mc_serial": None,
            "sw_version": None,
            "recipe_datetime": None,
            "lot_id": None,
            "source_file": str(source),
        }

        params: list[dict[str, object]] = []
        app_spec: dict[str, object] | None = None
        bsg_rows: list[dict[str, object]] = []
        rpm_limits: list[dict[str, object]] = []
        rpm_reference: list[dict[str, object]] = []

        parsed_files = 0
        failed_files = 0
        skipped_files = 0

        with extract_gzip_tar(source) as extracted_dir:
            files = sorted(path for path in extracted_dir.rglob("*") if path.is_file())
            bnd_files = [path for path in files if path.suffix.upper() == ".BND"]
            if not bnd_files:
                self.logger.error("no .BND file found in archive: %s", source)
                raise FileNotFoundError(f"BND file not found in archive: {source}")
            if len(bnd_files) > 1:
                self.logger.warning(
                    "multiple BND files found, using first one: %s",
                    bnd_files[0],
                )

            component_registry = BNDRegistryParser(logger=self.logger).parse(
                bnd_path=bnd_files[0],
                extracted_dir=extracted_dir,
            )
            pending_prms: list[_PendingPrm] = []
            parsed_prm_params: dict[str, list[dict[str, object]]] = {}

            for candidate in files:
                parser = self.registry.parser_for_file(candidate)
                if parser is None:
                    skipped_files += 1
                    self.logger.debug("skip unsupported file: %s", candidate)
                    continue

                try:
                    parsed = parser.parse(candidate)
                except Exception:  # noqa: BLE001
                    failed_files += 1
                    self.logger.exception("parse failed: file=%s", candidate)
                    continue

                parsed_files += 1
                file_type = candidate.suffix.lstrip(".").upper()
                file_params = list(parsed.params)

                bsg_rows.extend(parsed.bsg_rows)
                rpm_limits.extend(parsed.rpm_limits)
                rpm_reference.extend(parsed.rpm_reference)

                role = resolve_role(candidate.stem, file_type, component_registry)
                fallback_prefix = None
                if role is None and file_type in ROLE_REQUIRED_FILE_TYPES:
                    fallback_prefix = candidate.stem
                    self.logger.warning(
                        "fallback to file stem prefix for unresolved role: file=%s type=%s",
                        candidate,
                        file_type,
                    )

                if file_type == "PRM":
                    pending_prms.append(
                        _PendingPrm(
                            stem=candidate.stem,
                            file_path=candidate,
                            params=file_params,
                            role=role,
                            fallback_prefix=fallback_prefix,
                        )
                    )
                    parsed_prm_params[candidate.stem] = file_params
                else:
                    prefix = role or fallback_prefix
                    if prefix:
                        file_params = _prefix_params(file_params, prefix)
                    if file_type == "AID":
                        file_params = []
                    params.extend(file_params)

                if parsed.app_spec:
                    if app_spec is None:
                        app_spec = dict(parsed.app_spec)
                    else:
                        app_spec.update({k: v for k, v in parsed.app_spec.items() if v not in (None, "")})

                if candidate.suffix.upper() == ".BND":
                    bnd_metadata = extract_bnd_metadata(parsed.params)
                    import_record.update({k: v for k, v in bnd_metadata.items() if v is not None})

            ordered_prms = _ordered_prms(pending_prms, component_registry)
            drop_parms_2_stem: str | None = None
            if len(component_registry.parms_list) >= 2:
                first_parms = component_registry.parms_list[0]
                second_parms = component_registry.parms_list[1]
                if first_parms.stem in parsed_prm_params and second_parms.stem in parsed_prm_params:
                    if not should_keep_parms_2(first_parms, second_parms, parsed_prm_params):
                        drop_parms_2_stem = second_parms.stem

            for prm in ordered_prms:
                if prm.stem == drop_parms_2_stem:
                    continue
                prefix = prm.role or prm.fallback_prefix
                prm_params = prm.params
                if prefix:
                    prm_params = _prefix_params(prm_params, prefix)
                params.extend(prm_params)

        # Deduplicate params: same (file_type, param_name) keeps last occurrence.
        # Role-prefixed params are deduplicated after all parser outputs are merged.
        seen: dict[tuple[str, str], int] = {}
        for i, p in enumerate(params):
            seen[(str(p.get("file_type", "")), str(p.get("param_name", "")))] = i
        params = [params[i] for i in sorted(seen.values())]

        recipe_import_id: int | None = None
        if self.repository is not None:
            recipe_import_id = self.repository.save_recipe(
                import_record=import_record,
                params=params,
                app_spec=app_spec,
                bsg_rows=bsg_rows,
                rpm_limits=rpm_limits,
                rpm_reference=rpm_reference,
            )

        return PipelineResult(
            source_file=source,
            recipe_import_id=recipe_import_id,
            total_files=parsed_files + skipped_files + failed_files,
            parsed_files=parsed_files,
            skipped_files=skipped_files,
            failed_files=failed_files,
            parameter_count=len(params),
            bsg_count=len(bsg_rows),
            rpm_limits_count=len(rpm_limits),
            rpm_reference_count=len(rpm_reference),
        )
