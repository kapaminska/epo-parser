"""Tests for epo-konwersja.txt summary formatting and writing."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.conversion import ConversionResult
from domain.model import ParseWarning
from domain.summary import format_summary, write_summary


def test_format_summary_success_with_warnings() -> None:
    result = ConversionResult(
        source=Path("epo-odebrana-osobiscie.xml"),
        pdf_path=Path("epo-odebrana-osobiscie.pdf"),
        status="success",
        warnings=[
            ParseWarning(
                code="missing_city",
                message="Brak miejscowości adresata.",
            ),
        ],
    )

    text = format_summary([result])

    assert "Podsumowanie konwersji EPO" in text
    assert "Liczba plików: 1" in text
    assert "Plik: epo-odebrana-osobiscie.xml" in text
    assert "Status: sukces" in text
    assert "PDF: epo-odebrana-osobiscie.pdf" in text
    assert "Ostrzeżenia:" in text
    assert "Brak miejscowości adresata." in text


def test_format_summary_failure() -> None:
    result = ConversionResult(
        source=Path("broken.xml"),
        pdf_path=None,
        status="failed",
        error_message="Nierozpoznany format pliku XML.",
    )

    text = format_summary([result])

    assert "Plik: broken.xml" in text
    assert "Status: błąd" in text
    assert "PDF: brak" in text
    assert "Błąd: Nierozpoznany format pliku XML." in text


def test_format_summary_empty_results() -> None:
    text = format_summary([])

    assert "Podsumowanie konwersji EPO" in text
    assert "Brak plików XML w bieżącym katalogu." in text
    assert "Liczba plików: 0" not in text


def test_format_summary_multiple_results() -> None:
    results = [
        ConversionResult(
            source=Path("a.xml"),
            pdf_path=Path("a.pdf"),
            status="success",
        ),
        ConversionResult(
            source=Path("b.xml"),
            pdf_path=None,
            status="failed",
            error_message="Uszkodzony plik XML.",
        ),
    ]

    text = format_summary(results)

    assert "Liczba plików: 2" in text
    assert "Plik: a.xml" in text
    assert "Status: sukces" in text
    assert "Plik: b.xml" in text
    assert "Status: błąd" in text
    assert "Uszkodzony plik XML." in text


def test_write_summary_creates_file(tmp_path: Path) -> None:
    result = ConversionResult(
        source=tmp_path / "sample.xml",
        pdf_path=tmp_path / "sample.pdf",
        status="success",
    )

    output_path = write_summary(tmp_path, [result])

    assert output_path == tmp_path / "epo-konwersja.txt"
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Plik: sample.xml" in content
    assert "Status: sukces" in content


def test_write_summary_uses_suffix_on_collision(tmp_path: Path) -> None:
    (tmp_path / "epo-konwersja.txt").write_text("stare podsumowanie\n", encoding="utf-8")
    result = ConversionResult(
        source=tmp_path / "sample.xml",
        pdf_path=tmp_path / "sample.pdf",
        status="success",
    )

    output_path = write_summary(tmp_path, [result])

    assert output_path == tmp_path / "epo-konwersja (2).txt"
    assert (tmp_path / "epo-konwersja.txt").read_text(encoding="utf-8") == "stare podsumowanie\n"
