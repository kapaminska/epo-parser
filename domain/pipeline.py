"""XML → PDF conversion pipeline (single file and batch)."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from domain.conversion import ConversionResult
from domain.naming import resolve_output_path
from parsers.registry import ParseError, parse_epo_xml
from pdf.renderer import render_epo_pdf


def convert_xml_file(
    xml_path: Path,
    *,
    output_directory: Path | None = None,
) -> ConversionResult:
    """Convert one EPO XML file to PDF beside the source (or in *output_directory*)."""
    resolved = xml_path.resolve()
    target_dir = resolved.parent if output_directory is None else output_directory
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        document = parse_epo_xml(resolved)
    except ParseError as exc:
        return ConversionResult(
            source=resolved,
            pdf_path=None,
            status="failed",
            error_message=str(exc),
        )

    pdf_path = resolve_output_path(resolved, ".pdf", directory=target_dir)
    render_epo_pdf(document, pdf_path)

    tracking_number = None
    if document.shipments:
        tracking_number = document.shipments[0].tracking_number

    return ConversionResult(
        source=resolved,
        pdf_path=pdf_path,
        status="success",
        warnings=list(document.warnings),
        tracking_number=tracking_number,
    )


def convert_xml_files(xml_paths: Iterable[Path]) -> list[ConversionResult]:
    """Convert multiple EPO XML files; continue on per-file errors.

    Result order matches input order. An empty iterable yields an empty list.
    """
    return [convert_xml_file(path) for path in xml_paths]
