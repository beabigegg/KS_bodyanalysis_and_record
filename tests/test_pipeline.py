from __future__ import annotations

from pathlib import Path

from ksbody.pipeline import RecipePipeline

from tests.support import build_sample_recipe_archive


class _RepositoryStub:
    def __init__(self) -> None:
        self.saved: dict[str, object] | None = None

    def save_recipe(self, **kwargs: object) -> int:
        self.saved = dict(kwargs)
        return 42


def test_pipeline_processes_archive_end_to_end() -> None:
    repository = _RepositoryStub()
    pipeline = RecipePipeline(repository=repository)
    root_dir = Path(__file__).resolve().parents[1]
    source = build_sample_recipe_archive(root_dir / ".pytest-samples", "pja3406")

    result = pipeline.process(source)

    assert result.recipe_import_id == 42
    assert result.parsed_files >= 10
    assert result.failed_files == 0
    assert result.parameter_count >= 10
    assert result.bsg_count == 1
    assert result.rpm_limits_count == 1
    assert result.rpm_reference_count == 1

    assert repository.saved is not None
    assert repository.saved["app_spec"]["cap_manufacturer"] == "K&S"
    assert repository.saved["app_spec"]["wire_dia"] == "1.7"
    assert len(repository.saved["wir_group_map"]) == 2
