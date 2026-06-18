"""Tests for bundled PDF resource path resolution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from pdf.resources import package_resource


def test_package_resource_font_exists_in_dev_mode() -> None:
    font_path = package_resource("assets/DejaVuSans.ttf")
    assert font_path.is_file()


def test_package_resource_font_path_when_frozen(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    font_dir = tmp_path / "pdf" / "assets"
    font_dir.mkdir(parents=True)
    font_file = font_dir / "DejaVuSans.ttf"
    font_file.write_bytes(b"font")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert package_resource("assets/DejaVuSans.ttf") == font_file
