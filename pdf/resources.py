"""Resolve bundled resource paths in dev and PyInstaller frozen runtimes."""

from __future__ import annotations

import sys
from pathlib import Path


def package_resource(relative: str) -> Path:
    """Return an absolute path to a file shipped with the ``pdf`` package.

    In a PyInstaller one-file build, resources are extracted under
    ``sys._MEIPASS/pdf/`` (matching ``datas`` in ``epo-parser.spec``); in
    development, they live next to this module.
    """
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS) / "pdf"
    else:
        base = Path(__file__).resolve().parent
    return base / relative
