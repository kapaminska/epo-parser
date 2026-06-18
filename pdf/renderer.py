"""Render canonical EPO documents to readable PDF files."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from domain.model import (
    DeliveryEvent,
    EpoDocument,
    Operator,
    ParseWarning,
    PostalUnit,
    Recipient,
    Shipment,
)
from pdf.resources import package_resource

FONT_PATH = package_resource("assets/DejaVuSans.ttf")
# FR-005: inline legal disclaimer (not a per-page footer hook).
LEGAL_FOOTER = (
    "Niniejszy plik PDF stanowi wyłącznie wizualizację. "
    "Wiążącym dokumentem pozostaje oryginalny podpisany plik XML."
)
FOOTER_BLOCK_HEIGHT_MM = 15
EMPTY_VALUE = "—"


def render_epo_pdf(document: EpoDocument, output_path: Path) -> None:
    """Write a human-readable PDF for *document* to *output_path*."""
    pdf = _EpoPdf()
    pdf.add_page()
    pdf.set_font("DejaVu", size=16)
    pdf.cell(text="Elektroniczne Potwierdzenie Odbioru")
    pdf.ln(10)

    if document.creation_date:
        pdf.set_font("DejaVu", size=10)
        pdf.cell(text=f"Data utworzenia karty: {_display(document.creation_date)}")
        pdf.ln(8)

    for index, shipment in enumerate(document.shipments):
        if len(document.shipments) > 1:
            pdf.set_font("DejaVu", size=12)
            pdf.cell(text=f"Przesyłka {index + 1}")
            pdf.ln(6)
        _render_shipment(pdf, shipment)

    _render_warnings(pdf, document.warnings)
    _render_legal_footer(pdf)
    pdf.output(str(output_path))


class _EpoPdf(FPDF):
    """FPDF configured with embedded DejaVu for Polish text."""

    def __init__(self) -> None:
        super().__init__()
        self.add_font("DejaVu", "", str(FONT_PATH))
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(15, 15, 15)


def _render_shipment(pdf: _EpoPdf, shipment: Shipment) -> None:
    _section_heading(pdf, "Adresat")
    _render_recipient(pdf, shipment.recipient)

    _section_heading(pdf, "Identyfikatory przesyłki")
    _label_value(pdf, "Numer nadania", shipment.tracking_number)
    _label_value(pdf, "Data nadania", shipment.dispatch_date)
    _label_value(pdf, "Sygnatura", shipment.reference)
    _label_value(pdf, "Rodzaj", shipment.kind)

    _section_heading(pdf, "Zdarzenie doręczenia")
    _render_delivery_event(pdf, shipment.delivery_event)

    if shipment.postal_unit is not None:
        _section_heading(pdf, "Jednostka")
        _render_postal_unit(pdf, shipment.postal_unit)

    _section_heading(pdf, "Wydający")
    _render_operator(pdf, shipment.operator)

    if shipment.has_outer_signature:
        pdf.set_font("DejaVu", size=10)
        pdf.multi_cell(
            w=0,
            h=5,
            text="Informacja: w pliku XML obecny jest zewnętrzny podpis PKCS#7.",
        )
        pdf.ln(2)


def _render_recipient(pdf: _EpoPdf, recipient: Recipient) -> None:
    _label_value(pdf, "Nazwa", recipient.name)
    _label_value(pdf, "Kod pocztowy", recipient.postal_code)
    _label_value(pdf, "Miejscowość", recipient.city)
    _label_value(pdf, "Ulica", recipient.street)
    _label_value(pdf, "Numer domu", recipient.house_number)
    _label_value(pdf, "Numer lokalu", recipient.apartment)


def _render_delivery_event(pdf: _EpoPdf, event: DeliveryEvent) -> None:
    _label_value(pdf, "Status przesyłki", str(event.status_code))
    _label_value(pdf, "Brak doręczenia", str(event.non_delivery_code))
    _label_value(pdf, "Znacznik czasu systemu", event.system_timestamp)
    _label_value(
        pdf,
        "Awizo w placówce",
        str(event.awizo_at_parcel_location),
    )
    _label_value(
        pdf,
        "Awizo w miejscu zawiadomienia",
        str(event.awizo_at_notice_location),
    )
    _label_value(pdf, "Data awizo 1", event.awizo_date_1)
    _label_value(pdf, "Data awizo 2", event.awizo_date_2)
    _label_value(pdf, "Podpis odbiorcy", event.recipient_signature)


def _render_postal_unit(pdf: _EpoPdf, unit: PostalUnit) -> None:
    _label_value(pdf, "Nazwa", unit.name)
    _label_value(pdf, "Dział", unit.department)
    _label_value(pdf, "Miejscowość", unit.city)
    _label_value(pdf, "Kod pocztowy", unit.postal_code)
    _label_value(pdf, "Ulica", unit.street)
    _label_value(pdf, "Numer domu", unit.house_number)
    _label_value(pdf, "Numer lokalu", unit.apartment)


def _render_operator(pdf: _EpoPdf, operator: Operator) -> None:
    _label_value(
        pdf,
        "Imię i nazwisko",
        _join_name(operator.first_name, operator.last_name),
    )
    _label_value(pdf, "Placówka pocztowa", operator.post_office_name)
    _label_value(pdf, "Adres placówki", operator.post_office_address)


def _render_warnings(pdf: _EpoPdf, warnings: list[ParseWarning]) -> None:
    _section_heading(pdf, "Uwagi / ostrzeżenia")
    pdf.set_font("DejaVu", size=10)
    if warnings:
        for warning in warnings:
            pdf.cell(text=f"- {_display(warning.message)}")
            pdf.ln(5)
    else:
        pdf.cell(text="Brak uwag")
        pdf.ln(5)


def _render_legal_footer(pdf: _EpoPdf) -> None:
    """Render the FR-005 disclaimer inline after uwagi / ostrzeżenia."""
    if pdf.get_y() + FOOTER_BLOCK_HEIGHT_MM > pdf.page_break_trigger:
        pdf.add_page()
    pdf.ln(6)
    pdf.set_font("DejaVu", size=9)
    pdf.multi_cell(w=0, h=4, text=LEGAL_FOOTER)


def _section_heading(pdf: _EpoPdf, title: str) -> None:
    pdf.ln(4)
    pdf.set_font("DejaVu", size=12)
    pdf.cell(text=title)
    pdf.ln(6)


def _label_value(pdf: _EpoPdf, label: str, value: str | None) -> None:
    pdf.set_font("DejaVu", size=10)
    pdf.cell(text=f"{label}: {_display(value)}")
    pdf.ln(5)


def _display(value: str | None) -> str:
    if value is None or not str(value).strip():
        return EMPTY_VALUE
    return str(value)


def _join_name(first_name: str | None, last_name: str | None) -> str | None:
    parts = [part for part in (first_name, last_name) if part and part.strip()]
    if not parts:
        return None
    return " ".join(parts)
