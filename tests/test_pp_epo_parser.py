"""Parametrized golden tests for EPO XML parsers (karta EPO + CRD)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES_DIR, load_manifest
from helpers import assert_document_matches_golden


@pytest.mark.parametrize("entry", load_manifest(), ids=lambda entry: entry["id"])
def test_parse_matches_golden(entry: dict) -> None:
    parse_epo_xml = pytest.importorskip("parsers.registry").parse_epo_xml

    xml_path = FIXTURES_DIR / entry["xml"]
    expected_path = FIXTURES_DIR / entry["expected"]
    golden = yaml.safe_load(expected_path.read_text(encoding="utf-8"))

    actual = parse_epo_xml(Path(xml_path))
    assert_document_matches_golden(actual, golden)
