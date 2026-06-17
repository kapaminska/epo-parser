"""Parametrized golden tests for the PP e-Doręczenia parser.

S-01 handoff: remove ``@pytest.mark.skip``, implement ``parse_pp_epo`` in
``parsers.pp_edoreczenia``, and ensure all six manifest cases pass.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES_DIR, load_manifest
from helpers import assert_document_matches_golden


@pytest.mark.parametrize("entry", load_manifest(), ids=lambda entry: entry["id"])
def test_parse_matches_golden(entry: dict) -> None:
    parse_pp_epo = pytest.importorskip("parsers.pp_edoreczenia").parse_pp_epo

    xml_path = FIXTURES_DIR / entry["xml"]
    expected_path = FIXTURES_DIR / entry["expected"]
    golden = yaml.safe_load(expected_path.read_text(encoding="utf-8"))

    actual = parse_pp_epo(Path(xml_path))
    assert_document_matches_golden(actual, golden)
