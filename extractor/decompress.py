from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import tarfile
import tempfile
from typing import Iterator


class DecompressError(RuntimeError):
    """Raised when a recipe archive cannot be decompressed."""


@contextmanager
def extract_gzip_tar(source_file: str | Path) -> Iterator[Path]:
    source = Path(source_file)
    if not source.exists():
        raise DecompressError(f"Source archive not found: {source}")

    with tempfile.TemporaryDirectory(prefix="recipe_body_") as temp_dir:
        output = Path(temp_dir)
        try:
            with tarfile.open(source, mode="r:gz") as archive:
                archive.extractall(output)
        except (tarfile.TarError, OSError) as exc:
            raise DecompressError(f"Failed to decompress '{source}': {exc}") from exc

        yield output
