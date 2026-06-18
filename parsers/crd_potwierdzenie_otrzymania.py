"""CRD adapter for ``Dokument`` / wzór 10856/2021 — Potwierdzenie otrzymania."""

from __future__ import annotations

import re
from pathlib import Path

from lxml import etree

from domain.model import (
    Attachment,
    DeliveryEvent,
    EdeliveryReceipt,
    EpoDocument,
    Operator,
    Party,
    Recipient,
    Shipment,
)
from parsers.pp_edoreczenia import ParseError

CRD_NS = "http://crd.gov.pl/wzor/2021/09/01/10856/"
OSOBA_NS = "http://crd.gov.pl/xml/schematy/osoba/2009/11/16/"
DS_NS = "http://www.w3.org/2000/09/xmldsig#"

NS = {"c": CRD_NS, "o": OSOBA_NS, "ds": DS_NS}
ROOT_LOCAL_NAME = "Dokument"
REFERENCE_PATTERN = re.compile(r"ZW\.\d+\.\d+\.\d+\.\d+")


def parse_crd_potwierdzenie(path: Path) -> EpoDocument:
    """Parse a CRD ``Dokument`` receipt XML file into the canonical model.

    Args:
        path: Filesystem path to a CRD 10856/2021 receipt document.

    Returns:
        Canonical ``EpoDocument`` with one shipment and e-delivery fields.

    Raises:
        ParseError: When XML is malformed, root/namespace is wrong, or
            ``TrescDokumentu`` is missing.
    """
    try:
        tree = etree.parse(str(path))
    except etree.XMLSyntaxError as exc:
        raise ParseError(f"Nieprawidłowy XML: {exc}") from exc

    root = tree.getroot()
    _validate_root(root)

    tresc = root.find("c:TrescDokumentu", NS)
    if tresc is None:
        raise ParseError("Brak TrescDokumentu w dokumencie CRD.")

    document_title = _optional_text(tresc.find("c:DaneDokumentu/c:TytulDokumentu", NS))
    attachments = _parse_attachments(tresc)
    dane_wiadomosci = tresc.find("c:DaneWiadomosci", NS)

    shipment = Shipment(
        tracking_number=_optional_text(
            dane_wiadomosci.find("c:IdentyfikatorWiadomosci", NS)
        )
        if dane_wiadomosci is not None
        else None,
        dispatch_date=_optional_text(
            tresc.find("c:DataWyslania/c:DataNadaniaPrzesylki", NS)
        ),
        reference=_extract_reference(attachments),
        kind=None,
        recipient=_parse_recipient(tresc),
        delivery_event=_stub_delivery_event(),
        operator=_empty_operator(),
        postal_unit=None,
        has_outer_signature=root.find(".//ds:Signature", NS) is not None,
        sender=_parse_party(tresc.find("c:DaneNadawcy", NS)),
        attachments=attachments,
        edelivery_receipt=_parse_edelivery_receipt(tresc),
        proof_id=_optional_text(
            dane_wiadomosci.find("c:IdentyfikatorDowoduPotwierdzenia", NS)
        )
        if dane_wiadomosci is not None
        else None,
    )

    return EpoDocument(
        creation_date=None,
        shipments=[shipment],
        warnings=[],
        document_title=document_title,
    )


def _validate_root(root: etree._Element) -> None:
    local_name = etree.QName(root.tag).localname
    namespace = etree.QName(root.tag).namespace
    if local_name != ROOT_LOCAL_NAME or namespace != CRD_NS:
        raise ParseError(
            "Nierozpoznany format XML: oczekiwano Dokument "
            f"(namespace {CRD_NS!r})."
        )


def _optional_text(element: etree._Element | None) -> str | None:
    if element is None:
        return None
    text = (element.text or "").strip()
    return text or None


def _parse_party(container: etree._Element | None) -> Party | None:
    if container is None:
        return None

    strona = container.find("c:StronaKorespondencji", NS)
    party_kind = _optional_text(strona.find("c:Rodzaj", NS)) if strona is not None else None
    name = _party_name(strona)
    edelivery_address = _optional_text(container.find("c:AdresEDoreczen", NS))

    if party_kind is None and name is None and edelivery_address is None:
        return None

    return Party(
        party_kind=party_kind,
        name=name,
        edelivery_address=edelivery_address,
    )


def _party_name(strona: etree._Element | None) -> str | None:
    if strona is None:
        return None

    legal_name = _optional_text(strona.find("c:OsobaPrawna/c:NazwaPodmiotu", NS))
    if legal_name is not None:
        return legal_name

    osoba = strona.find("c:OsobaFizyczna", NS)
    if osoba is None:
        return None

    parts = [
        value
        for value in (
            _optional_text(osoba.find("o:Imie", NS)),
            _optional_text(osoba.find("o:Nazwisko", NS)),
        )
        if value
    ]
    return " ".join(parts) if parts else None


def _parse_recipient(tresc: etree._Element) -> Recipient:
    container = tresc.find("c:DaneAdresata", NS)
    strona = container.find("c:StronaKorespondencji", NS) if container is not None else None

    return Recipient(
        name=_party_name(strona),
        postal_code=None,
        city=None,
        street=None,
        house_number=None,
        apartment=None,
        edelivery_address=_optional_text(container.find("c:AdresEDoreczen", NS))
        if container is not None
        else None,
        party_kind=_optional_text(strona.find("c:Rodzaj", NS)) if strona is not None else None,
    )


def _parse_attachments(tresc: etree._Element) -> tuple[Attachment, ...]:
    attachments: list[Attachment] = []
    for dane in tresc.findall("c:DaneZalaczniki/c:DaneZalacznika", NS):
        attrs: dict[str, str | None] = {}
        for atrybut in dane.findall("c:AtrybutZalacznika", NS):
            attr_name = atrybut.get("nazwaAtrybutu")
            if attr_name:
                attrs[attr_name] = _optional_text(atrybut.find("c:WartoscAtrybutu", NS))

        size_text = attrs.get("RozmiarZalacznika")
        attachments.append(
            Attachment(
                attachment_id=attrs.get("IdZalacznika"),
                name=attrs.get("NazwaZalacznika"),
                size_bytes=int(size_text) if size_text is not None else None,
                is_message_body=attrs.get("TrescWiadomosci") == "Tak",
            )
        )
    return tuple(attachments)


def _extract_reference(attachments: tuple[Attachment, ...]) -> str | None:
    for attachment in attachments:
        if attachment.name is None:
            continue
        match = REFERENCE_PATTERN.search(attachment.name)
        if match is not None:
            return match.group(0)
    return None


def _parse_edelivery_receipt(tresc: etree._Element) -> EdeliveryReceipt:
    dane_dokumentu = tresc.find("c:DaneDokumentu", NS)
    data_wyslania = tresc.find("c:DataWyslania", NS)
    data_odbioru = tresc.find("c:DataOdbioru", NS)
    dane_wiadomosci = tresc.find("c:DaneWiadomosci", NS)

    return EdeliveryReceipt(
        description=_optional_text(dane_dokumentu.find("c:OpisDokumentu", NS))
        if dane_dokumentu is not None
        else None,
        dispatch_date=_optional_text(data_wyslania.find("c:DataNadaniaPrzesylki", NS))
        if data_wyslania is not None
        else None,
        dispatch_acceptance_date=_optional_text(
            data_wyslania.find("c:DataAkceptacjiNadaniaPrzesylki", NS)
        )
        if data_wyslania is not None
        else None,
        made_available_date=_optional_text(
            data_odbioru.find("c:DataUdostepnieniaDoOdbioru", NS)
        )
        if data_odbioru is not None
        else None,
        delivered_to_recipient_date=_optional_text(
            data_odbioru.find("c:DataPrzekazaniaAdresatowi", NS)
        )
        if data_odbioru is not None
        else None,
        delivery_mode=_optional_text(dane_wiadomosci.find("c:TrybDoreczenia", NS))
        if dane_wiadomosci is not None
        else None,
        legal_footer=_optional_text(tresc.find("c:Stopka", NS)),
    )


def _stub_delivery_event() -> DeliveryEvent:
    return DeliveryEvent(
        status_code=0,
        non_delivery_code=0,
        system_timestamp=None,
        awizo_at_parcel_location=0,
        awizo_at_notice_location=0,
        awizo_date_1=None,
        awizo_date_2=None,
        recipient_signature=None,
    )


def _empty_operator() -> Operator:
    return Operator(
        first_name=None,
        last_name=None,
        post_office_name=None,
        post_office_address=None,
    )
