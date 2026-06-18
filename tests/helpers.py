"""Golden comparison helpers for parser integration tests."""

from __future__ import annotations

from typing import Any

from domain.model import (
    Attachment,
    DeliveryEvent,
    EdeliveryReceipt,
    EpoDocument,
    Operator,
    ParseWarning,
    Party,
    PostalUnit,
    Recipient,
    Shipment,
)


def _assert_optional_object(
    actual: Any,
    expected: dict[str, Any] | None,
    cls: type,
    path: str,
) -> None:
    if expected is None:
        if actual is not None:
            raise AssertionError(f"{path}: expected null, got {actual!r}")
        return
    if actual is None:
        raise AssertionError(f"{path}: expected object, got null")
    for field_name, expected_value in expected.items():
        actual_value = getattr(actual, field_name)
        if actual_value != expected_value:
            raise AssertionError(
                f"{path}.{field_name}: expected {expected_value!r}, got {actual_value!r}"
            )


def _assert_attachments_match(
    actual: tuple[Attachment, ...],
    expected: list[dict[str, Any]],
    path: str,
) -> None:
    if len(actual) != len(expected):
        raise AssertionError(
            f"{path}: expected {len(expected)} attachment(s), got {len(actual)}"
        )
    for index, (actual_attachment, expected_attachment) in enumerate(
        zip(actual, expected, strict=True)
    ):
        _assert_optional_object(
            actual_attachment,
            expected_attachment,
            Attachment,
            f"{path}[{index}]",
        )


def assert_document_matches_golden(actual: EpoDocument, golden: dict[str, Any]) -> None:
    """Compare a parsed ``EpoDocument`` against golden YAML ``document`` data."""
    document = golden["document"]
    if actual.creation_date != document.get("creation_date"):
        raise AssertionError(
            "document.creation_date: "
            f"expected {document.get('creation_date')!r}, got {actual.creation_date!r}"
        )
    if actual.document_title != document.get("document_title"):
        raise AssertionError(
            "document.document_title: "
            f"expected {document.get('document_title')!r}, got {actual.document_title!r}"
        )

    expected_shipments = document.get("shipments", [])
    if len(actual.shipments) != len(expected_shipments):
        raise AssertionError(
            "document.shipments: "
            f"expected {len(expected_shipments)} item(s), got {len(actual.shipments)}"
        )

    for index, (actual_shipment, expected_shipment) in enumerate(
        zip(actual.shipments, expected_shipments, strict=True)
    ):
        prefix = f"document.shipments[{index}]"
        for field_name in (
            "tracking_number",
            "dispatch_date",
            "reference",
            "kind",
            "has_outer_signature",
            "proof_id",
        ):
            actual_value = getattr(actual_shipment, field_name)
            expected_value = expected_shipment.get(field_name)
            if actual_value != expected_value:
                raise AssertionError(
                    f"{prefix}.{field_name}: expected {expected_value!r}, got {actual_value!r}"
                )

        _assert_optional_object(
            actual_shipment.recipient,
            expected_shipment.get("recipient"),
            Recipient,
            f"{prefix}.recipient",
        )
        _assert_optional_object(
            actual_shipment.delivery_event,
            expected_shipment.get("delivery_event"),
            DeliveryEvent,
            f"{prefix}.delivery_event",
        )
        _assert_optional_object(
            actual_shipment.operator,
            expected_shipment.get("operator"),
            Operator,
            f"{prefix}.operator",
        )
        _assert_optional_object(
            actual_shipment.postal_unit,
            expected_shipment.get("postal_unit"),
            PostalUnit,
            f"{prefix}.postal_unit",
        )
        _assert_optional_object(
            actual_shipment.sender,
            expected_shipment.get("sender"),
            Party,
            f"{prefix}.sender",
        )
        _assert_optional_object(
            actual_shipment.edelivery_receipt,
            expected_shipment.get("edelivery_receipt"),
            EdeliveryReceipt,
            f"{prefix}.edelivery_receipt",
        )
        _assert_attachments_match(
            actual_shipment.attachments,
            expected_shipment.get("attachments", []),
            f"{prefix}.attachments",
        )

    expected_warnings = golden.get("expected_warnings", [])
    if len(actual.warnings) != len(expected_warnings):
        raise AssertionError(
            "warnings: "
            f"expected {len(expected_warnings)} item(s), got {len(actual.warnings)}"
        )
    for index, (actual_warning, expected_warning) in enumerate(
        zip(actual.warnings, expected_warnings, strict=True)
    ):
        if actual_warning.code != expected_warning["code"]:
            raise AssertionError(
                f"warnings[{index}].code: "
                f"expected {expected_warning['code']!r}, got {actual_warning.code!r}"
            )
        if actual_warning.message != expected_warning["message"]:
            raise AssertionError(
                f"warnings[{index}].message: "
                f"expected {expected_warning['message']!r}, got {actual_warning.message!r}"
            )
