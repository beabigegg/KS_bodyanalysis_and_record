from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging

from db.repository import RecipeRepository
from extractor.decompress import extract_gzip_tar
from extractor.metadata import extract_bnd_metadata, extract_metadata
from parsers.registry import ParserRegistry


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
                params.extend(parsed.params)
                bsg_rows.extend(parsed.bsg_rows)
                rpm_limits.extend(parsed.rpm_limits)
                rpm_reference.extend(parsed.rpm_reference)

                if parsed.app_spec:
                    if app_spec is None:
                        app_spec = dict(parsed.app_spec)
                    else:
                        app_spec.update({k: v for k, v in parsed.app_spec.items() if v not in (None, "")})

                if candidate.suffix.upper() == ".BND":
                    bnd_metadata = extract_bnd_metadata(parsed.params)
                    import_record.update({k: v for k, v in bnd_metadata.items() if v is not None})

        # Deduplicate params: same (file_type, param_name) keeps last occurrence
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
