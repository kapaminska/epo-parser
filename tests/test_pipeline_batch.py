"""Tests for batch XML → PDF conversion pipeline."""

from __future__ import annotations

import shutil
from pathlib import Path

from conftest import FIXTURES_DIR
from domain.pipeline import convert_xml_files


def test_convert_xml_files_continue_on_error(tmp_path: Path) -> None:
    valid_xml = FIXTURES_DIR / "epo-odebrana-osobiscie.xml"
    invalid_xml = tmp_path / "broken.xml"
    shutil.copy(valid_xml, tmp_path / "valid.xml")
    invalid_xml.write_text("not valid xml", encoding="utf-8")

    results = convert_xml_files([tmp_path / "valid.xml", invalid_xml])

    assert len(results) == 2
    assert results[0].status == "success"
    assert results[0].pdf_path is not None
    assert results[1].status == "failed"
    assert results[1].pdf_path is None
    assert results[1].error_message


def test_convert_xml_files_empty_input() -> None:
    assert convert_xml_files([]) == []


def test_convert_xml_files_preserves_order(tmp_path: Path) -> None:
    fixture = FIXTURES_DIR / "epo-odebrana-osobiscie.xml"
    shutil.copy(fixture, tmp_path / "first.xml")
    shutil.copy(fixture, tmp_path / "second.xml")

    results = convert_xml_files([tmp_path / "first.xml", tmp_path / "second.xml"])

    assert [result.source.name for result in results] == ["first.xml", "second.xml"]
    assert all(result.status == "success" for result in results)


def test_convert_xml_files_mixed_karta_epo_and_crd(tmp_path: Path) -> None:
    karta_xml = FIXTURES_DIR / "epo-odebrana-osobiscie.xml"
    crd_xml = FIXTURES_DIR / "crd-osoba-fizyczna.xml"
    shutil.copy(karta_xml, tmp_path / "epo-odebrana-osobiscie.xml")
    shutil.copy(crd_xml, tmp_path / crd_xml.name)

    results = convert_xml_files([tmp_path / "epo-odebrana-osobiscie.xml", tmp_path / crd_xml.name])

    assert len(results) == 2
    assert all(result.status == "success" for result in results)
    assert all(result.pdf_path is not None for result in results)
