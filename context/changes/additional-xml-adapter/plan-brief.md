# S-06: Adapter CRD Potwierdzenie otrzymania — skrót planu

> Pełny plan: `context/changes/additional-xml-adapter/plan.md`

## What & Why

Użytkownicy LP dostają z e-Doręczeń PP nie tylko karty `TabletKartaEpo`, ale też CRD „Potwierdzenie otrzymania” (wzór 10856). Bez adaptera te pliki kończą błędem „nierozpoznany format”. Slice dodaje drugi parser, rejestr formatów i PDF z nadawcą/adresatem AE — zgodnie z FR-003 i decyzją „CRD w MVP”.

## Starting Point

S-01 działa dla 6 fixture `karta_epo_v1`. W `tests/fixtures/` są 3 produkcyjne XML CRD (poza manifestem). Pipeline woła tylko `parse_pp_epo`. Model nie ma nadawcy ani pól e-doręczeń.

## Desired End State

`parse_epo_xml` rozpoznaje oba formaty. `pytest` — 9 golden parser + testy PDF CRD. CLI generuje czytelny PDF i txt dla plików CRD obok istniejących EPO pocztowych.

## Key Decisions Made

| Decyzja | Wybór | Dlaczego (1 zdanie) | Źródło |
| -------- | ----- | ------------------- | ------ |
| Złożoność slice | Niższa niż HIGH — pełny vertical bez over-engineeringu | Parser + PDF w jednym change, bez osobnego typu dokumentu | Plan |
| Model | Rozszerzyć `Shipment` / `EpoDocument` | Jeden renderer z gałęzią; zgodne z architekturą kanoniczną | Plan |
| Golden karta_epo | Dopisać nowe pola (`null` / `[]`) we wszystkich 6 YAML | Jeden kontrakt testowy, walidacja kształtu dataclass | Plan |
| Sygnatura CRD | Regex `ZW.\d+.\d+.\d+.\d+` z nazw załączników | Odzwierciedla praktykę LP w nazwach plików decyzji | Plan |
| Dispatch | `parsers/registry.py` → `parse_epo_xml` | S-01 przewidywał rejestr adapterów; pipeline bez logiki formatu | Plan |
| Zakres PDF | Pełny layout CRD w tym change | FR-003 wymaga nadawcy; użytkownik wybrał full vertical | Plan |

## Scope

**W zakresie:**
- Rozszerzenie `domain/model.py`
- `parsers/crd_potwierdzenie_otrzymania.py` + `parsers/registry.py`
- 3 wpisy manifest + golden CRD + aktualizacja 6 golden
- Gałąź PDF CRD + testy
- Podpięcie pipeline i testów golden (9 przypadków)

**Poza zakresem:**
- Weryfikacja crypto XAdES (S-04)
- ePUAP / inne źródła
- Zmiana formatu summary txt
- Aktualizacja roadmap (opcjonalnie osobno)

## Architecture / Approach

```
plik.xml ──► parsers/registry.parse_epo_xml
                 ├── TabletKartaEpo ──► parse_pp_epo ──┐
                 └── Dokument CRD ──► parse_crd ──────┤
                                                      ▼
                                              EpoDocument ──► pdf/renderer ──► .pdf
                                                      │
domain/pipeline ──► domain/summary ──► epo-konwersja.txt
```

## Phases at a Glance

| Faza | Dostarcza | Główne ryzyko |
| ---- | --------- | ------------- |
| 1. Model + korpus | Typy, manifest, 9× golden shape | Literówki w wartościach CRD YAML |
| 2. Parser + registry | 9/9 golden parser | Namespace osoby (`ns8:Imie`) |
| 3. PDF CRD | Layout + test pypdf | Zbyt gęsty PDF przy wielu załącznikach |
| 4. E2E | `pytest -v`, batch CLI | Regresja layoutu karta EPO |

**Wymagania wstępne:** S-01 zaimplementowany (tak)
**Szacunek:** ~2–3 sesje (4 fazy)

## Open Risks & Assumptions

- Tylko wzór CRD 10856/2021 w korpusie — inne wersje wzoru wymagają nowego wariantu.
- `DeliveryEvent` dla CRD to stub — nie mieszać z kodami pocztowymi w PDF.
- Roadmap nadal mówi „post-MVP” dla S-06 — produktowo CRD jest w MVP (do zsynchronizowania w docs).

## Success Criteria (Summary)

- 9/9 golden parser; full `pytest -v` green.
- Trzy fixture CRD → PDF + txt przez CLI.
- Mieszany batch karta EPO + CRD bez błędów formatu.
