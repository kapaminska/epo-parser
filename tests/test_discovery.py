"""Tests for flat XML discovery in a directory."""

from __future__ import annotations

from pathlib import Path

from domain.discovery import discover_xml_files


def test_discover_xml_files_flat_sorted_ignores_subdirs(tmp_path: Path) -> None:
    (tmp_path / "b.xml").write_text("<root/>", encoding="utf-8")
    (tmp_path / "a.xml").write_text("<root/>", encoding="utf-8")
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "nested.xml").write_text("<root/>", encoding="utf-8")

    discovered = discover_xml_files(tmp_path)

    assert [path.name for path in discovered] == ["a.xml", "b.xml"]


def test_discover_xml_files_skips_non_files(tmp_path: Path) -> None:
    (tmp_path / "valid.xml").write_text("<root/>", encoding="utf-8")
    (tmp_path / "not-xml.txt").write_text("text", encoding="utf-8")

    discovered = discover_xml_files(tmp_path)

    assert [path.name for path in discovered] == ["valid.xml"]


def test_discover_xml_files_empty_directory(tmp_path: Path) -> None:
    assert discover_xml_files(tmp_path) == []
