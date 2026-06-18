"""Parser registry — single entry point for all supported EPO XML formats."""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from domain.model import EpoDocument
from parsers.crd_potwierdzenie_otrzymania import CRD_NS, parse_crd_potwierdzenie
from parsers.pp_edoreczenia import KARTA_EPO_NS, ParseError, parse_pp_epo


def parse_epo_xml(path: Path) -> EpoDocument:
    """Parse a supported EPO XML file into the canonical model.

    Routes ``TabletKartaEpo`` (Karta EPO) and CRD ``Dokument`` receipts
    to their respective adapters.

    Args:
        path: Filesystem path to an EPO XML document.

    Raises:
        ParseError: When XML is malformed or the root element is not a
            supported format.
    """
    try:
        tree = etree.parse(str(path))
    except etree.XMLSyntaxError as exc:
        raise ParseError(f"Nieprawidłowy XML: {exc}") from exc

    root = tree.getroot()
    local_name = etree.QName(root.tag).localname
    namespace = etree.QName(root.tag).namespace

    if local_name == "TabletKartaEpo" and namespace == KARTA_EPO_NS:
        return parse_pp_epo(path)

    if local_name == "Dokument" and namespace == CRD_NS:
        return parse_crd_potwierdzenie(path)

    raise ParseError(
        "Nierozpoznany format XML: oczekiwano TabletKartaEpo "
        f"(namespace {KARTA_EPO_NS!r}) lub Dokument CRD (namespace {CRD_NS!r})."
    )
