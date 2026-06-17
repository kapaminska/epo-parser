"""Non-destructive output path naming (PRD FR-003 / FR-004).

When a target PDF or summary file already exists, append a numeric suffix
`` (2)``, `` (3)``, … rather than overwriting.
"""

from __future__ import annotations

from pathlib import Path

SUMMARY_BASENAME = "epo-konwersja.txt"


def resolve_output_path(
    source: Path,
    extension: str,
    directory: Path | None = None,
) -> Path:
    """Return a free output path with the same stem as *source*.

    Args:
        source: Input XML path whose stem becomes the output basename.
        extension: Target extension, with or without leading dot (e.g. ``.pdf``).
        directory: Output directory; defaults to the source file's parent.
    """
    if not extension.startswith("."):
        extension = f".{extension}"
    target_dir = source.parent if directory is None else directory
    return _resolve_with_suffix(target_dir / f"{source.stem}{extension}")


def resolve_summary_path(directory: Path) -> Path:
    """Return a free path for the operation summary text file in *directory*."""
    return _resolve_with_suffix(directory / SUMMARY_BASENAME)


def _resolve_with_suffix(base_path: Path) -> Path:
    """First free path: *base_path*, then ``stem (2).ext``, ``stem (3).ext``, …"""
    if not base_path.exists():
        return base_path

    parent = base_path.parent
    stem = base_path.stem
    suffix = base_path.suffix
    counter = 2
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
