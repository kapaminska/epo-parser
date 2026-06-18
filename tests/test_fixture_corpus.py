"""Structural integrity tests for the EPO XML fixture corpus."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest
import yaml
from lxml import etree

from conftest import CRD_POTWIERDZENIE_NS, FIXTURES_DIR, KARTA_EPO_NS, load_manifest
from domain.model import (
    Attachment,
    DeliveryEvent,
    EdeliveryReceipt,
    Operator,
    ParseWarning,
    Party,
    PostalUnit,
    Recipient,
    Shipment,
)


def _top_level_xml_files() -> list[Path]:
    return sorted(FIXTURES_DIR.glob("*.xml"))


def _manifest_entries() -> list[dict]:
    return load_manifest()


def _load_golden(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _assert_dict_keys_match_dataclass(data: dict, cls: type, path: str) -> None:
    expected_keys = {field.name for field in fields(cls)}
    actual_keys = set(data.keys())
    if actual_keys != expected_keys:
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        raise AssertionError(
            f"{path}: key mismatch (missing={sorted(missing)}, extra={sorted(extra)})"
        )


def _validate_attachments(attachments: object, path: str) -> None:
    assert isinstance(attachments, list), f"{path}.attachments must be a list"
    for index, attachment in enumerate(attachments):
        _assert_dict_keys_match_dataclass(
            attachment, Attachment, f"{path}.attachments[{index}]"
        )


def _validate_document_shape(document: dict, path: str = "document") -> None:
    assert set(document.keys()) == {"creation_date", "document_title", "shipments"}, (
        f"{path}: expected keys creation_date, document_title, shipments"
    )
    shipments = document.get("shipments")
    assert isinstance(shipments, list), f"{path}.shipments must be a list"
    assert shipments, f"{path}.shipments must not be empty"

    for index, shipment in enumerate(shipments):
        shipment_path = f"{path}.shipments[{index}]"
        _assert_dict_keys_match_dataclass(shipment, Shipment, shipment_path)
        _assert_dict_keys_match_dataclass(shipment["recipient"], Recipient, f"{shipment_path}.recipient")
        _assert_dict_keys_match_dataclass(
            shipment["delivery_event"], DeliveryEvent, f"{shipment_path}.delivery_event"
        )
        _assert_dict_keys_match_dataclass(shipment["operator"], Operator, f"{shipment_path}.operator")
        postal_unit = shipment.get("postal_unit")
        if postal_unit is not None:
            _assert_dict_keys_match_dataclass(postal_unit, PostalUnit, f"{shipment_path}.postal_unit")
        sender = shipment.get("sender")
        if sender is not None:
            _assert_dict_keys_match_dataclass(sender, Party, f"{shipment_path}.sender")
        edelivery_receipt = shipment.get("edelivery_receipt")
        if edelivery_receipt is not None:
            _assert_dict_keys_match_dataclass(
                edelivery_receipt, EdeliveryReceipt, f"{shipment_path}.edelivery_receipt"
            )
        _validate_attachments(shipment.get("attachments"), shipment_path)


def test_manifest_lists_all_xml_fixtures() -> None:
    manifest_xml = {entry["xml"] for entry in _manifest_entries()}
    disk_xml = {path.name for path in _top_level_xml_files()}
    assert manifest_xml == disk_xml


@pytest.mark.parametrize("entry", _manifest_entries(), ids=lambda entry: entry["id"])
def test_each_fixture_is_well_formed_xml(entry: dict) -> None:
    xml_path = FIXTURES_DIR / entry["xml"]
    etree.parse(str(xml_path))


@pytest.mark.parametrize("entry", _manifest_entries(), ids=lambda entry: entry["id"])
def test_each_fixture_has_parseable_root(entry: dict) -> None:
    xml_path = FIXTURES_DIR / entry["xml"]
    root = etree.parse(str(xml_path)).getroot()
    variant = entry["schema_variant"]

    if variant == "karta_epo_v1":
        assert root.tag.endswith("TabletKartaEpo")
        assert (
            root.nsmap.get(root.prefix or "mstns") == KARTA_EPO_NS
            or KARTA_EPO_NS in root.nsmap.values()
        )
        return

    if variant == "crd_potwierdzenie_otrzymania_v1":
        assert root.tag.endswith("Dokument")
        assert (
            root.nsmap.get(root.prefix) == CRD_POTWIERDZENIE_NS
            or CRD_POTWIERDZENIE_NS in root.nsmap.values()
        )
        return

    pytest.fail(f"Unknown schema_variant: {variant!r}")


@pytest.mark.parametrize("entry", _manifest_entries(), ids=lambda entry: entry["id"])
def test_each_fixture_has_golden_yaml(entry: dict) -> None:
    expected_path = FIXTURES_DIR / entry["expected"]
    assert expected_path.is_file()


@pytest.mark.parametrize("entry", _manifest_entries(), ids=lambda entry: entry["id"])
def test_golden_yaml_matches_document_schema(entry: dict) -> None:
    golden = _load_golden(FIXTURES_DIR / entry["expected"])
    assert golden["id"] == entry["id"]
    assert golden["schema_variant"] == entry["schema_variant"]
    _validate_document_shape(golden["document"])


@pytest.mark.parametrize("entry", _manifest_entries(), ids=lambda entry: entry["id"])
def test_golden_warnings_are_lists(entry: dict) -> None:
    golden = _load_golden(FIXTURES_DIR / entry["expected"])
    warnings = golden.get("expected_warnings")
    assert isinstance(warnings, list)
    for index, warning in enumerate(warnings):
        _assert_dict_keys_match_dataclass(warning, ParseWarning, f"expected_warnings[{index}]")
