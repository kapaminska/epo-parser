"""EPO Parser CLI — convert XML files to PDF and write a batch summary txt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_MISSING_FILE_MESSAGE = "Nie znaleziono pliku wejściowego."


def _configure_stdio_utf8() -> None:
    """Avoid Windows console UnicodeEncodeError when printing Polish CLI text."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass


def resolve_summary_directory(paths: list[Path]) -> Path:
    """Return the directory for ``epo-konwersja.txt`` for explicit CLI paths.

    When all paths share the same parent, use that parent; otherwise use cwd.
    """
    if not paths:
        return Path.cwd()
    parents = {path.resolve().parent for path in paths}
    if len(parents) == 1:
        return next(iter(parents))
    return Path.cwd()


def _process_explicit_paths(paths: list[Path]) -> list:
    from domain.conversion import ConversionResult
    from domain.pipeline import convert_xml_file

    results: list[ConversionResult] = []
    for path in paths:
        if not path.exists():
            results.append(
                ConversionResult(
                    source=path,
                    pdf_path=None,
                    status="failed",
                    error_message=_MISSING_FILE_MESSAGE,
                )
            )
        else:
            results.append(convert_xml_file(path))
    return results


def main(argv: list[str] | None = None) -> int:
    """Convert XML files to PDF and write ``epo-konwersja.txt``.

    With no arguments, discovers ``*.xml`` in the current directory (flat scan).
    With one or more paths, converts each file in a single batch.
    """
    _configure_stdio_utf8()
    parser = argparse.ArgumentParser(
        description="Konwertuj pliki XML EPO (e-Doręczenia PP) na PDF.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Ścieżki do plików XML EPO (puste = wszystkie *.xml w bieżącym katalogu)",
    )
    args = parser.parse_args(argv)

    from domain.discovery import discover_xml_files
    from domain.pipeline import convert_xml_files
    from domain.summary import write_summary

    if not args.paths:
        summary_dir = Path.cwd()
        xml_paths = discover_xml_files(summary_dir)
        results = convert_xml_files(xml_paths)
    else:
        summary_dir = resolve_summary_directory(args.paths)
        results = _process_explicit_paths(args.paths)

    write_summary(summary_dir, results)

    if not results or any(result.status == "failed" for result in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
