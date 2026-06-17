"""Tests for main.py CLI helpers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = PROJECT_ROOT / "main.py"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import main, resolve_summary_directory


def test_resolve_summary_directory_same_parent(tmp_path: Path) -> None:
    paths = [tmp_path / "a.xml", tmp_path / "b.xml"]

    assert resolve_summary_directory(paths) == tmp_path


def test_resolve_summary_directory_different_parents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    dir_one = tmp_path / "dir1"
    dir_two = tmp_path / "dir2"
    dir_one.mkdir()
    dir_two.mkdir()

    assert resolve_summary_directory([dir_one / "a.xml", dir_two / "b.xml"]) == tmp_path


def test_resolve_summary_directory_empty_paths() -> None:
    assert resolve_summary_directory([]) == Path.cwd()


def test_main_importable() -> None:
    assert callable(main)


def test_main_help() -> None:
    completed = subprocess.run(
        [sys.executable, str(MAIN_PY), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode == 0
    assert "Konwertuj pliki XML EPO" in completed.stdout
