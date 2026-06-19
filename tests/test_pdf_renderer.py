"""Tests for canonical EPO PDF rendering."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pypdf import PdfReader

from conftest import FIXTURES_DIR, load_manifest
from pdf.renderer import LEGAL_FOOTER, render_epo_pdf

PDF_FIXTURE_IDS = [
    "epo-odebrana-osobiscie",
    "epo-jednostka-nadlesnictwo",
    "epo-minimal-puste-pola",
]

SECTION_HEADINGS = [
    "Adresat",
    "Identyfikatory przesyłki",
    "Zdarzenie doręczenia",
    "Wydający",
    "Uwagi / ostrzeżenia",
]


def _manifest_by_id() -> dict[str, dict]:
    return {entry["id"]: entry for entry in load_manifest()}


def _extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _normalize_pdf_text(text: str) -> str:
    return " ".join(text.split())


@pytest.mark.parametrize("fixture_id", PDF_FIXTURE_IDS)
def test_render_epo_pdf_contains_core_sections(
    fixture_id: str,
    tmp_path: Path,
) -> None:
    parse_pp_epo = pytest.importorskip("parsers.pp_edoreczenia").parse_pp_epo
    entry = _manifest_by_id()[fixture_id]
    document = parse_pp_epo(FIXTURES_DIR / entry["xml"])
    output_path = tmp_path / "out.pdf"

    render_epo_pdf(document, output_path)

    assert output_path.exists()
    text = _extract_pdf_text(output_path)
    assert "Elektroniczne Potwierdzenie Odbioru" in text
    for heading in SECTION_HEADINGS:
        assert heading in text


@pytest.mark.parametrize(
    "fixture_id",
    ["epo-odebrana-osobiscie", "epo-minimal-puste-pola"],
)
def test_render_epo_pdf_legal_footer_text_and_order(
    fixture_id: str,
    tmp_path: Path,
) -> None:
    parse_pp_epo = pytest.importorskip("parsers.pp_edoreczenia").parse_pp_epo
    entry = _manifest_by_id()[fixture_id]
    document = parse_pp_epo(FIXTURES_DIR / entry["xml"])
    output_path = tmp_path / f"{fixture_id}.pdf"

    render_epo_pdf(document, output_path)

    text = _extract_pdf_text(output_path)
    normalized = _normalize_pdf_text(text)
    assert _normalize_pdf_text(LEGAL_FOOTER) in normalized
    uwagi_index = normalized.index("Uwagi / ostrzeżenia")
    disclaimer_index = normalized.index(
        "Niniejszy plik PDF stanowi wyłącznie wizualizację"
    )
    assert uwagi_index < disclaimer_index


def test_render_epo_pdf_contains_tracking_number_and_polish_diacritics(
    tmp_path: Path,
) -> None:
    parse_pp_epo = pytest.importorskip("parsers.pp_edoreczenia").parse_pp_epo
    entry = _manifest_by_id()["epo-odebrana-osobiscie"]
    document = parse_pp_epo(FIXTURES_DIR / entry["xml"])
    output_path = tmp_path / "odebrana.pdf"

    render_epo_pdf(document, output_path)

    text = _extract_pdf_text(output_path)
    assert "PUH7443447077999" in text
    assert "ZIELIŃSKA" in text
    assert "Piaseczno" in text or "PIASECZNO" in text


def test_render_epo_pdf_shows_postal_unit_section(tmp_path: Path) -> None:
    parse_pp_epo = pytest.importorskip("parsers.pp_edoreczenia").parse_pp_epo
    entry = _manifest_by_id()["epo-jednostka-nadlesnictwo"]
    document = parse_pp_epo(FIXTURES_DIR / entry["xml"])
    output_path = tmp_path / "nadlesnictwo.pdf"

    render_epo_pdf(document, output_path)

    text = _extract_pdf_text(output_path)
    assert "Jednostka" in text
    assert "Nadleśnictwo Sulejówek" in text
    assert "DĄBROWSKI" in text


def test_render_epo_pdf_includes_warning_messages(tmp_path: Path) -> None:
    parse_pp_epo = pytest.importorskip("parsers.pp_edoreczenia").parse_pp_epo
    entry = _manifest_by_id()["epo-minimal-puste-pola"]
    golden = yaml.safe_load(
        (FIXTURES_DIR / entry["expected"]).read_text(encoding="utf-8")
    )
    document = parse_pp_epo(FIXTURES_DIR / entry["xml"])
    output_path = tmp_path / "minimal.pdf"

    render_epo_pdf(document, output_path)

    text = _extract_pdf_text(output_path)
    for warning in golden["expected_warnings"]:
        assert warning["message"] in text


@pytest.mark.parametrize("fixture_id", ["crd-osoba-fizyczna"])
def test_render_crd_pdf_contains_edelivery_sections(
    fixture_id: str,
    tmp_path: Path,
) -> None:
    parse_epo_xml = pytest.importorskip("parsers.registry").parse_epo_xml
    entry = _manifest_by_id()[fixture_id]
    document = parse_epo_xml(FIXTURES_DIR / entry["xml"])
    output_path = tmp_path / f"{fixture_id}.pdf"

    render_epo_pdf(document, output_path)

    text = _extract_pdf_text(output_path)
    assert "Potwierdzenie otrzymania" in text
    assert "Nadawca" in text
    assert "NADAWCA TESTOWY LP" in text
    assert "PPSA-E-aaaa1111-bbbb-2222-cccc-ddddeeee0001" in text
    assert "ZW.999.1.901" in text
    assert "XAdES" in text
