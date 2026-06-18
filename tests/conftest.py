"""Shared pytest fixtures for the EPO XML corpus."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
KARTA_EPO_NS = "http://msepo.gov.pl/epo/XSD/KartaEPO.xsd"
CRD_POTWIERDZENIE_NS = "http://crd.gov.pl/wzor/2021/09/01/10856/"


def load_manifest() -> list[dict[str, Any]]:
    """Load ``manifest.yaml`` entries linking XML fixtures to golden YAML."""
    manifest_path = FIXTURES_DIR / "manifest.yaml"
    entries = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError(f"Expected manifest list in {manifest_path}")
    return entries
