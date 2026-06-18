"""XML source adapters mapping EPO schemas to the canonical domain model."""

from parsers.crd_potwierdzenie_otrzymania import parse_crd_potwierdzenie
from parsers.pp_edoreczenia import ParseError, parse_pp_epo
from parsers.registry import parse_epo_xml

__all__ = [
    "ParseError",
    "parse_crd_potwierdzenie",
    "parse_epo_xml",
    "parse_pp_epo",
]
