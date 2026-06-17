"""Canonical EPO document model for PP e-Doręczenia adapters.

Types describe structured fields extracted from ``TabletKartaEpo`` XML
(``KartaEPO.xsd``). No sender/nadawca field — not present in current fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParseWarning:
    """Non-fatal parse issue surfaced to the user and summary txt."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class Recipient:
    """Delivery addressee address block."""

    name: str | None
    postal_code: str | None
    city: str | None
    street: str | None
    house_number: str | None
    apartment: str | None


@dataclass(frozen=True, slots=True)
class Operator:
    """Postal clerk who issued the shipment (``Wydajacy`` attributes)."""

    first_name: str | None
    last_name: str | None
    post_office_name: str | None
    post_office_address: str | None


@dataclass(frozen=True, slots=True)
class PostalUnit:
    """Forestry unit block (``TabletJednostkaMS`` / Nadleśnictwo)."""

    name: str | None
    department: str | None
    city: str | None
    postal_code: str | None
    street: str | None
    house_number: str | None
    apartment: str | None


@dataclass(frozen=True, slots=True)
class DeliveryEvent:
    """Delivery status, awizo flags/dates, and recipient signature."""

    status_code: int
    non_delivery_code: int
    system_timestamp: str | None
    awizo_at_parcel_location: int
    awizo_at_notice_location: int
    awizo_date_1: str | None
    awizo_date_2: str | None
    recipient_signature: str | None


@dataclass(frozen=True, slots=True)
class Shipment:
    """Single shipment on an EPO card (MVP fixtures contain exactly one)."""

    tracking_number: str | None
    dispatch_date: str | None
    reference: str | None
    kind: str | None
    recipient: Recipient
    delivery_event: DeliveryEvent
    operator: Operator
    postal_unit: PostalUnit | None
    has_outer_signature: bool


@dataclass(frozen=True, slots=True)
class EpoDocument:
    """Canonical representation of one EPO card."""

    creation_date: str | None
    shipments: list[Shipment]
    warnings: list[ParseWarning]
