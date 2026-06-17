"""Discover EPO XML files in a directory for batch processing."""

from __future__ import annotations

from pathlib import Path


def discover_xml_files(directory: Path) -> list[Path]:
    """Return a sorted list of ``*.xml`` files directly inside *directory*.

    Only immediate children are considered (no recursion). Entries that are not
    regular files are skipped. Content is not validated — that is the parser's job.
    """
    return sorted(
        (path for path in directory.glob("*.xml") if path.is_file()),
        key=lambda path: path.name,
    )
