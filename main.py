"""EPO Parser CLI — convert a single XML file to PDF and write a summary txt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from domain.conversion import ConversionResult
from domain.pipeline import convert_xml_file
from domain.summary import write_summary


def main(argv: list[str] | None = None) -> int:
    """Convert one XML path to PDF and write ``epo-konwersja.txt`` beside it."""
    parser = argparse.ArgumentParser(
        description="Konwertuj plik XML EPO (e-Doręczenia PP) na PDF.",
    )
    parser.add_argument(
        "xml_path",
        type=Path,
        help="Ścieżka do pliku XML EPO",
    )
    args = parser.parse_args(argv)
    xml_path: Path = args.xml_path

    if not xml_path.exists():
        summary_dir = xml_path.parent if xml_path.parent.exists() else Path.cwd()
        result = ConversionResult(
            source=xml_path,
            pdf_path=None,
            status="failed",
            error_message="Nie znaleziono pliku wejściowego.",
        )
        write_summary(summary_dir, [result])
        return 1

    result = convert_xml_file(xml_path)
    write_summary(result.source.parent, [result])
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
