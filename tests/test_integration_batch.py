"""End-to-end integration tests for directory batch conversion."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import FIXTURES_DIR, load_manifest
from domain.pipeline import convert_xml_files

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = PROJECT_ROOT / "main.py"

_BATCH_FIXTURE_IDS = (
    "epo-odebrana-osobiscie",
    "epo-awizo-w-placowce",
    "epo-jednostka-nadlesnictwo",
)


def _run_main(
    args: list[str] | None = None,
    *,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(MAIN_PY)]
    if args:
        command.extend(args)
    return subprocess.run(
        command,
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


def _copy_batch_fixtures(directory: Path) -> list[str]:
    names: list[str] = []
    for entry_id in _BATCH_FIXTURE_IDS:
        entry = _manifest_entry(entry_id)
        xml_name = Path(entry["xml"]).name
        shutil.copy(FIXTURES_DIR / entry["xml"], directory / xml_name)
        names.append(xml_name)
    return names


def test_integration_batch_zero_arg(tmp_path: Path) -> None:
    xml_names = _copy_batch_fixtures(tmp_path)

    completed = _run_main(cwd=tmp_path)

    assert completed.returncode == 0, completed.stderr
    for xml_name in xml_names:
        assert (tmp_path / f"{Path(xml_name).stem}.pdf").exists()

    summary = (tmp_path / "epo-konwersja.txt").read_text(encoding="utf-8")
    assert "Liczba plików: 3" in summary
    for xml_name in xml_names:
        assert xml_name in summary
        assert "Status: sukces" in summary


def test_integration_batch_empty_folder(tmp_path: Path) -> None:
    completed = _run_main(cwd=tmp_path)

    assert completed.returncode == 1
    assert list(tmp_path.glob("*.pdf")) == []
    summary = (tmp_path / "epo-konwersja.txt").read_text(encoding="utf-8")
    assert "Brak plików XML w bieżącym katalogu." in summary


def test_integration_batch_mixed_success_and_failure(tmp_path: Path) -> None:
    entry = _manifest_entry("epo-odebrana-osobiscie")
    valid_name = Path(entry["xml"]).name
    shutil.copy(FIXTURES_DIR / entry["xml"], tmp_path / valid_name)
    (tmp_path / "broken.xml").write_text("", encoding="utf-8")

    completed = _run_main(cwd=tmp_path)

    assert completed.returncode == 1
    assert (tmp_path / "epo-odebrana-osobiscie.pdf").exists()
    assert list(tmp_path.glob("broken*.pdf")) == []

    summary = (tmp_path / "epo-konwersja.txt").read_text(encoding="utf-8")
    assert "Liczba plików: 2" in summary
    assert valid_name in summary
    assert "broken.xml" in summary
    assert summary.count("Status: sukces") == 1
    assert summary.count("Status: błąd") == 1


def test_integration_batch_multi_arg_cli(tmp_path: Path) -> None:
    entry_one = _manifest_entry("epo-odebrana-osobiscie")
    entry_two = _manifest_entry("epo-awizo-w-placowce")
    xml_one = Path(entry_one["xml"]).name
    xml_two = Path(entry_two["xml"]).name
    shutil.copy(FIXTURES_DIR / entry_one["xml"], tmp_path / xml_one)
    shutil.copy(FIXTURES_DIR / entry_two["xml"], tmp_path / xml_two)

    completed = _run_main([xml_one, xml_two], cwd=tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / "epo-odebrana-osobiscie.pdf").exists()
    assert (tmp_path / "epo-awizo-w-placowce.pdf").exists()
    summary = (tmp_path / "epo-konwersja.txt").read_text(encoding="utf-8")
    assert "Liczba plików: 2" in summary
    assert xml_one in summary
    assert xml_two in summary


def test_integration_batch_second_run_uses_summary_suffix(tmp_path: Path) -> None:
    entry = _manifest_entry("epo-odebrana-osobiscie")
    xml_name = Path(entry["xml"]).name
    shutil.copy(FIXTURES_DIR / entry["xml"], tmp_path / xml_name)

    assert _run_main(cwd=tmp_path).returncode == 0
    assert _run_main(cwd=tmp_path).returncode == 0

    assert (tmp_path / "epo-konwersja.txt").exists()
    assert (tmp_path / "epo-konwersja (2).txt").exists()


def test_integration_batch_zero_arg_ignores_subfolder_xml(tmp_path: Path) -> None:
    entry = _manifest_entry("epo-odebrana-osobiscie")
    xml_name = Path(entry["xml"]).name
    shutil.copy(FIXTURES_DIR / entry["xml"], tmp_path / xml_name)

    subdir = tmp_path / "sub"
    subdir.mkdir()
    shutil.copy(FIXTURES_DIR / entry["xml"], subdir / "nested.xml")

    completed = _run_main(cwd=tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / "epo-odebrana-osobiscie.pdf").exists()
    assert list(subdir.glob("*.pdf")) == []
    summary = (tmp_path / "epo-konwersja.txt").read_text(encoding="utf-8")
    assert "Liczba plików: 1" in summary
    assert "nested.xml" not in summary


@pytest.mark.slow
@pytest.mark.skip(reason="dev-only performance smoke; run with pytest -m slow")
def test_batch_performance_smoke_50_files(tmp_path: Path) -> None:
    entry = _manifest_entry("epo-odebrana-osobiscie")
    xml_paths: list[Path] = []
    for index in range(50):
        target = tmp_path / f"epo-batch-{index:02d}.xml"
        shutil.copy(FIXTURES_DIR / entry["xml"], target)
        xml_paths.append(target)

    started = time.perf_counter()
    results = convert_xml_files(xml_paths)
    elapsed = time.perf_counter() - started

    assert len(results) == 50
    assert all(result.status == "success" for result in results)
    assert elapsed < 5.0, f"batch of 50 took {elapsed:.2f}s"
