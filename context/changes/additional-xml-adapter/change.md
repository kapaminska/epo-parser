---
change_id: additional-xml-adapter
title: CRD Potwierdzenie otrzymania adapter (S-06)
status: implementing
created: 2026-06-18
updated: 2026-06-18
archived_at: null
---

## Notes

Pierwsza instancja roadmap S-06. Format: CRD `Dokument` / wzór 10856/2021 („Potwierdzenie otrzymania”) z e-Doręczeń PP.

Fixture produkcyjne (już w `tests/fixtures/`, poza manifestem):
- `ZW.224.1.856.2025 (Potwierdzenie otrzymania).xml`
- `Znak sprawy_ ZW.224.1.840.2025 (Potwierdzenie otrzymania).xml`
- `Znak sprawy_ ZW.224.1.932.2025 (Potwierdzenie otrzymania).xml`

Decyzja produktowa: format wchodzi do MVP (nie post-MVP).

### Dostarczone w tym change

- Rozszerzony model kanoniczny (`Party`, `Attachment`, `EdeliveryReceipt`, pola e-doręczeń na `Shipment`/`Recipient`).
- Adapter `parsers/crd_potwierdzenie_otrzymania.py` + dispatch `parsers/registry.parse_epo_xml`.
- Korpus 9 fixture (6 karta EPO + 3 CRD) z golden YAML.
- PDF z gałęzią CRD (nadawca, adresat AE, załączniki, daty, XAdES info).
- Pipeline i testy golden/parser/PDF/batch obsługują oba formaty.

### Decyzje implementacyjne

- `DeliveryEvent` dla CRD to stub zerowy — sekcja pocztowa „Zdarzenie doręczenia” nie renderuje się w PDF CRD.
- Sygnatura (`reference`): regex `ZW\.\d+\.\d+\.\d+\.\d+` z nazw załączników; brak dopasowania → `null`.
- Weryfikacja crypto podpisu XAdES pozostaje poza zakresem (S-04).
