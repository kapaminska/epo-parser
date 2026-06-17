"""PP e-Doręczenia adapter for ``TabletKartaEpo`` / ``KartaEPO.xsd``."""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from domain.model import (
    DeliveryEvent,
    EpoDocument,
    Operator,
    ParseWarning,
    PostalUnit,
    Recipient,
    Shipment,
)

KARTA_EPO_NS = "http://msepo.gov.pl/epo/XSD/KartaEPO.xsd"
NS = {"m": KARTA_EPO_NS}
ROOT_LOCAL_NAME = "TabletKartaEpo"


class ParseError(Exception):
    """Raised for malformed XML or documents that are not PP ``TabletKartaEpo``."""


def parse_pp_epo(path: Path) -> EpoDocument:
    """Parse a PP e-Doręczenia EPO XML file into the canonical model.

    Args:
        path: Filesystem path to a ``TabletKartaEpo`` XML document.

    Returns:
        Canonical ``EpoDocument`` with best-effort field extraction and
        ``ParseWarning`` entries for missing optional data.

    Raises:
        ParseError: When XML is not well-formed or the root element is not
            ``TabletKartaEpo`` in the Karta EPO namespace.
    """
    try:
        tree = etree.parse(str(path))
    except etree.XMLSyntaxError as exc:
        raise ParseError(f"Nieprawidłowy XML: {exc}") from exc

    root = tree.getroot()
    _validate_root(root)

    creation_date = _optional_text(root.find("m:CreationDate", NS))
    shipments = [_parse_shipment(node) for node in root.findall(".//m:TabletPrzesylka", NS)]
    warnings = _collect_warnings(shipments)

    return EpoDocument(
        creation_date=creation_date,
        shipments=shipments,
        warnings=warnings,
    )


def _validate_root(root: etree._Element) -> None:
    local_name = etree.QName(root.tag).localname
    namespace = etree.QName(root.tag).namespace
    if local_name != ROOT_LOCAL_NAME or namespace != KARTA_EPO_NS:
        raise ParseError(
            "Nierozpoznany format XML: oczekiwano TabletKartaEpo "
            f"(namespace {KARTA_EPO_NS!r})."
        )


def _optional_text(element: etree._Element | None) -> str | None:
    if element is None:
        return None
    text = (element.text or "").strip()
    return text or None


def _optional_int(element: etree._Element | None, default: int = 0) -> int:
    text = _optional_text(element)
    if text is None:
        return default
    return int(text)


def _optional_attr(element: etree._Element | None, name: str) -> str | None:
    if element is None:
        return None
    value = (element.get(name) or "").strip()
    return value or None


def _parse_recipient(shipment: etree._Element) -> Recipient:
    return Recipient(
        name=_optional_text(shipment.find("m:Adresat", NS)),
        postal_code=_optional_text(shipment.find("m:KodPocztowy", NS)),
        city=_optional_text(shipment.find("m:Miejscowosc", NS)),
        street=_optional_text(shipment.find("m:Ulica", NS)),
        house_number=_optional_text(shipment.find("m:Dom", NS)),
        apartment=_optional_text(shipment.find("m:Lokal", NS)),
    )


def _parse_operator(shipment: etree._Element) -> Operator:
    wydajacy = shipment.find("m:Wydajacy", NS)
    return Operator(
        first_name=_optional_attr(wydajacy, "Imie"),
        last_name=_optional_attr(wydajacy, "Nazwisko"),
        post_office_name=_optional_attr(wydajacy, "NazwaPlacowki"),
        post_office_address=_optional_attr(wydajacy, "AdresPlacowki"),
    )


def _operator_is_empty(operator: Operator) -> bool:
    return all(
        value is None
        for value in (
            operator.first_name,
            operator.last_name,
            operator.post_office_name,
            operator.post_office_address,
        )
    )


def _parse_postal_unit(shipment: etree._Element) -> PostalUnit | None:
    unit = shipment.find("m:TabletJednostkaMS", NS)
    if unit is None:
        return None

    parsed = PostalUnit(
        name=_optional_text(unit.find("m:NazwaJednostki", NS)),
        department=_optional_text(unit.find("m:Wydzial", NS)),
        city=_optional_text(unit.find("m:Miasto", NS)),
        postal_code=_optional_text(unit.find("m:KodPocztowy", NS)),
        street=_optional_text(unit.find("m:Ulica", NS)),
        house_number=_optional_text(unit.find("m:Dom", NS)),
        apartment=_optional_text(unit.find("m:Lokal", NS)),
    )
    if all(
        value is None
        for value in (
            parsed.name,
            parsed.department,
            parsed.city,
            parsed.postal_code,
            parsed.street,
            parsed.house_number,
            parsed.apartment,
        )
    ):
        return None
    return parsed


def _parse_delivery_event(shipment: etree._Element) -> DeliveryEvent:
    return DeliveryEvent(
        status_code=_optional_int(shipment.find("m:StatusPrzesylki", NS)),
        non_delivery_code=_optional_int(shipment.find("m:BrakDoreczenia", NS)),
        system_timestamp=_optional_text(shipment.find("m:SystemowaDataOznaczenia", NS)),
        awizo_at_parcel_location=_optional_int(shipment.find("m:AwizoMiejscePrzesylki", NS)),
        awizo_at_notice_location=_optional_int(
            shipment.find("m:AwizoMiejsceZawiadomienia", NS)
        ),
        awizo_date_1=_optional_text(shipment.find("m:DataAwizo1", NS)),
        awizo_date_2=_optional_text(shipment.find("m:DataAwizo2", NS)),
        recipient_signature=_optional_text(shipment.find("m:Podpis", NS)),
    )


def _has_outer_signature(shipment: etree._Element) -> bool:
    wrapper = shipment.getparent()
    if wrapper is None:
        return False
    outer_signature = wrapper.find("m:Podpis", NS)
    return _optional_text(outer_signature) is not None


def _parse_shipment(shipment: etree._Element) -> Shipment:
    return Shipment(
        tracking_number=_optional_text(shipment.find("m:NumerNadania", NS)),
        dispatch_date=_optional_text(shipment.find("m:DataNadania", NS)),
        reference=_optional_text(shipment.find("m:Sygnatura", NS)),
        kind=_optional_text(shipment.find("m:Rodzaj", NS)),
        recipient=_parse_recipient(shipment),
        delivery_event=_parse_delivery_event(shipment),
        operator=_parse_operator(shipment),
        postal_unit=_parse_postal_unit(shipment),
        has_outer_signature=_has_outer_signature(shipment),
    )


def _collect_warnings(shipments: list[Shipment]) -> list[ParseWarning]:
    """Emit document-level warnings in deterministic order for the first shipment."""
    if not shipments:
        return []

    shipment = shipments[0]
    warnings: list[ParseWarning] = []

    if shipment.recipient.city is None:
        warnings.append(
            ParseWarning(code="missing_city", message="Brak miejscowości adresata")
        )
    if shipment.reference is None:
        warnings.append(ParseWarning(code="missing_reference", message="Brak sygnatury"))
    if _operator_is_empty(shipment.operator):
        warnings.append(
            ParseWarning(code="missing_operator", message="Brak danych wydającego")
        )
    elif shipment.kind is None:
        warnings.append(
            ParseWarning(code="missing_kind", message="Brak rodzaju przesyłki")
        )

    return warnings
