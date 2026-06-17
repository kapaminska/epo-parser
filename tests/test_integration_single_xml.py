"""End-to-end integration tests for single-file XML → PDF + summary txt."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import FIXTURES_DIR, load_manifest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = PROJECT_ROOT / "main.py"


def _run_main(xml_path: Path, *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MAIN_PY), str(xml_path)],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _manifest_entry(entry_id: str) -> dict:
    for entry in load_manifest():
        if entry["id"] == entry_id:
            return entry
    raise KeyError(entry_id)


def test_integration_success_creates_pdf_and_summary(tmp_path: Path) -> None:
    entry = _manifest_entry("epo-odebrana-osobiscie")
    xml_name = Path(entry["xml"]).name
    shutil.copy(FIXTURES_DIR / entry["xml"], tmp_path / xml_name)

    completed = _run_main(tmp_path / xml_name, cwd=tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / "epo-odebrana-osobiscie.pdf").exists()
    summary_path = tmp_path / "epo-konwersja.txt"
    assert summary_path.exists()
    summary = summary_path.read_text(encoding="utf-8")
    assert xml_name in summary
    assert "PUH7443447077999" in summary
    assert "Status: sukces" in summary


def test_integration_second_run_uses_suffixes(tmp_path: Path) -> None:
    entry = _manifest_entry("epo-odebrana-osobiscie")
    xml_name = Path(entry["xml"]).name
    shutil.copy(FIXTURES_DIR / entry["xml"], tmp_path / xml_name)
    xml_path = tmp_path / xml_name

    assert _run_main(xml_path, cwd=tmp_path).returncode == 0
    assert _run_main(xml_path, cwd=tmp_path).returncode == 0

    assert (tmp_path / "epo-odebrana-osobiscie.pdf").exists()
    assert (tmp_path / "epo-odebrana-osobiscie (2).pdf").exists()
    assert (tmp_path / "epo-konwersja.txt").exists()
    assert (tmp_path / "epo-konwersja (2).txt").exists()


def test_integration_ezd_filename_with_spaces(tmp_path: Path) -> None:
    entry = _manifest_entry("epo-ezd-nieodebrana")
    xml_name = entry["xml"]
    shutil.copy(FIXTURES_DIR / entry["xml"], tmp_path / xml_name)

    completed = _run_main(tmp_path / xml_name, cwd=tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / f"{Path(xml_name).stem}.pdf").exists()
    summary = (tmp_path / "epo-konwersja.txt").read_text(encoding="utf-8")
    assert xml_name in summary
    assert "PUH7443447077100" in summary


def test_integration_invalid_input_no_pdf_and_error_summary(tmp_path: Path) -> None:
    bad_path = tmp_path / "not-epo.txt"
    bad_path.write_text("to nie jest xml\n", encoding="utf-8")

    completed = _run_main(bad_path, cwd=tmp_path)

    assert completed.returncode == 1
    assert list(tmp_path.glob("*.pdf")) == []
    summary = (tmp_path / "epo-konwersja.txt").read_text(encoding="utf-8")
    assert "not-epo.txt" in summary
    assert "Status: błąd" in summary
    assert "Błąd:" in summary


def test_integration_empty_file_fails_without_pdf(tmp_path: Path) -> None:
    empty_xml = tmp_path / "empty.xml"
    empty_xml.write_text("", encoding="utf-8")

    completed = _run_main(empty_xml, cwd=tmp_path)

    assert completed.returncode == 1
    assert list(tmp_path.glob("*.pdf")) == []
    summary = (tmp_path / "epo-konwersja.txt").read_text(encoding="utf-8")
    assert "Status: błąd" in summary


def test_integration_missing_file_exit_code_one(tmp_path: Path) -> None:
    missing = tmp_path / "missing.xml"

    completed = _run_main(missing, cwd=tmp_path)

    assert completed.returncode == 1
    summary = (tmp_path / "epo-konwersja.txt").read_text(encoding="utf-8")
    assert "missing.xml" in summary
    assert "Nie znaleziono pliku wejściowego." in summary
