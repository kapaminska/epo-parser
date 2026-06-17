"""Text summary writer for batch conversion feedback (``epo-konwersja.txt``)."""

from __future__ import annotations

from pathlib import Path

from domain.conversion import ConversionResult
from domain.naming import resolve_summary_path


def format_summary(results: list[ConversionResult]) -> str:
    """Build a human-readable Polish summary for one or more conversion results."""
    lines: list[str] = [
        "Podsumowanie konwersji EPO",
        f"Liczba plików: {len(results)}",
        "",
    ]

    for index, result in enumerate(results):
        if index > 0:
            lines.append("")

        lines.append(f"Plik: {result.source.name}")
        if result.status == "success":
            lines.append("Status: sukces")
        else:
            lines.append("Status: błąd")

        if result.pdf_path is not None:
            lines.append(f"PDF: {result.pdf_path.name}")
        else:
            lines.append("PDF: brak")

        if result.error_message:
            lines.append(f"Błąd: {result.error_message}")

        if result.warnings:
            lines.append("Ostrzeżenia:")
            for warning in result.warnings:
                lines.append(f"  - {warning.message}")

    return "\n".join(lines) + "\n"


def write_summary(directory: Path, results: list[ConversionResult]) -> Path:
    """Write the summary text file using non-destructive naming rules."""
    output_path = resolve_summary_path(directory)
    output_path.write_text(format_summary(results), encoding="utf-8")
    return output_path
