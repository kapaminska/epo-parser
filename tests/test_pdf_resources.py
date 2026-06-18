"""Tests for bundled PDF resource path resolution."""

from __future__ import annotations

from pdf.resources import package_resource


def test_package_resource_font_exists_in_dev_mode() -> None:
    font_path = package_resource("assets/DejaVuSans.ttf")
    assert font_path.is_file()
