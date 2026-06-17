"""Tests for non-destructive PDF and summary path naming."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.naming import resolve_output_path, resolve_summary_path


def test_resolve_output_path_no_collision(tmp_path: Path) -> None:
    source = tmp_path / "foo.xml"
    source.touch()

    result = resolve_output_path(source, ".pdf")

    assert result == tmp_path / "foo.pdf"
    assert not result.exists()


def test_resolve_output_path_second_collision(tmp_path: Path) -> None:
    source = tmp_path / "foo.xml"
    source.touch()
    (tmp_path / "foo.pdf").touch()

    result = resolve_output_path(source, ".pdf")

    assert result == tmp_path / "foo (2).pdf"


def test_resolve_output_path_third_collision(tmp_path: Path) -> None:
    source = tmp_path / "foo.xml"
    source.touch()
    (tmp_path / "foo.pdf").touch()
    (tmp_path / "foo (2).pdf").touch()

    result = resolve_output_path(source, ".pdf")

    assert result == tmp_path / "foo (3).pdf"


def test_resolve_output_path_custom_directory(tmp_path: Path) -> None:
    source = tmp_path / "input" / "bar.xml"
    source.parent.mkdir(parents=True)
    source.touch()
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    result = resolve_output_path(source, "pdf", directory=out_dir)

    assert result == out_dir / "bar.pdf"


def test_resolve_output_path_preserves_stem_with_spaces(tmp_path: Path) -> None:
    source = tmp_path / "Wiadomość EZD (test).xml"
    source.touch()

    result = resolve_output_path(source, ".pdf")

    assert result == tmp_path / "Wiadomość EZD (test).pdf"


def test_resolve_summary_path_no_collision(tmp_path: Path) -> None:
    result = resolve_summary_path(tmp_path)

    assert result == tmp_path / "epo-konwersja.txt"


def test_resolve_summary_path_second_collision(tmp_path: Path) -> None:
    (tmp_path / "epo-konwersja.txt").touch()

    result = resolve_summary_path(tmp_path)

    assert result == tmp_path / "epo-konwersja (2).txt"


def test_resolve_summary_path_third_collision(tmp_path: Path) -> None:
    (tmp_path / "epo-konwersja.txt").touch()
    (tmp_path / "epo-konwersja (2).txt").touch()

    result = resolve_summary_path(tmp_path)

    assert result == tmp_path / "epo-konwersja (3).txt"
