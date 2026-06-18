# S-06: Adapter CRD Potwierdzenie otrzymania — plan implementacji

## Overview

Dodać drugi adapter XML (CRD `Dokument` / wzór 10856/2021 — „Potwierdzenie otrzymania”) obok istniejącego `TabletKartaEpo`, z rejestrem parserów, rozszerzeniem modelu kanonicznego, korpusem fixture (3 pliki produkcyjne już w `tests/fixtures/`) oraz layoutem PDF dla e-doręczeń. Slice realizuje roadmap **S-06** dla pierwszego dodatkowego formatu w MVP.

## Current State Analysis

S-01 (`single-xml-to-pdf-and-txt`) jest zaimplementowany: `parse_pp_epo`, `domain/pipeline.py`, `pdf/renderer.py`, 6 golden `karta_epo_v1`, pełna suite pytest. Pipeline woła wyłącznie `parse_pp_epo` — brak dispatchu formatów.

W `tests/fixtures/` leżą **3 nieśledzone pliki CRD** (poza manifestem):
- `ZW.224.1.856.2025 (Potwierdzenie otrzymania).xml` — adresat osoba fizyczna, 2 załączniki
- `Znak sprawy_ ZW.224.1.840.2025 (Potwierdzenie otrzymania).xml` — adresat osoba prawna, 3 załączniki
- `Znak sprawy_ ZW.224.1.932.2025 (Potwierdzenie otrzymania).xml` — adresat osoba fizyczna, brak `ZW.*` w załącznikach (reference = null)

Root CRD: `Dokument` @ `http://crd.gov.pl/wzor/2021/09/01/10856/`. Treść biznesowa w `TrescDokumentu`. Osoby fizyczne używają namespace `http://crd.gov.pl/xml/schematy/osoba/2009/11/16/` (`Imie`, `Nazwisko`).

### Key Discoveries:

- Model kanoniczny (`domain/model.py`) nie ma nadawcy ani pól e-doręczeń — CRD wymaga rozszerzenia, nie samego mapowania na `DeliveryEvent`.
- `tests/test_fixture_corpus.py` wymaga synchronizacji manifest ↔ dysk i walidacji kształtu golden vs dataclass.
- `tests/helpers.py` porównuje golden tylko dla pól `karta_epo_v1` — trzeba rozszerzyć o nowe pola Shipment/Recipient/EpoDocument.
- PRD FR-003 wymaga sekcji nadawca/adresat w PDF — CRD to pierwszy format, który nadawcę dostarcza.

## Desired End State

Po zakończeniu slice:

1. `python main.py "tests/fixtures/ZW.224.1.856.2025 (Potwierdzenie otrzymania).xml"` → PDF + wpis w `epo-konwersja.txt` (sufiks ` (2)` przy kolizji).
2. Batch w folderze z mieszanką `TabletKartaEpo` + CRD konwertuje oba formaty bez błędu „nierozpoznany format”.
3. `pytest -v` green — 9 przypadków golden parsera (6 + 3 CRD), testy korpusu, testy PDF dla co najmniej jednego CRD.
4. PDF CRD zawiera: tytuł „Potwierdzenie otrzymania”, Nadawca, Adresat (AE), identyfikatory, daty doręczenia, załączniki, uwagi, stopkę prawną, informację o podpisie XAdES.

### Verification

```bash
pip install -e ".[dev]"
pytest -v
python main.py "tests/fixtures/ZW.224.1.856.2025 (Potwierdzenie otrzymania).xml"
python main.py "tests/fixtures/epo-odebrana-osobiscie.xml"
```

## What We're NOT Doing

- Weryfikacja kryptograficzna podpisu XAdES (S-04 — tylko flaga/informacja o obecności).
- Parsowanie metadanych certyfikatu poza `has_outer_signature`.
- ePUAP UPO ani inne źródła spoza PP e-doręczeń.
- Zmiana formatu `epo-konwersja.txt` poza obsługą nowego typu pliku (ten sam wpis sukces/błąd).
- Aktualizacja roadmap w tym slice (opcjonalnie osobny commit docs).
- PDF/A, GUI, sieć.

## Implementation Approach

Cztery fazy z checkpointem manualnym po fazie 3. Rozszerzyć model w `domain/` (bez importu lxml/fpdf2). Nowy adapter w `parsers/crd_potwierdzenie_otrzymania.py`. Dispatch w `parsers/registry.py` (`parse_epo_xml`). Pipeline i testy golden wołają registry, nie bezpośrednio `parse_pp_epo`. PDF: gałąź gdy `shipment.edelivery_receipt is not None` — bez osobnego modułu renderera.

## Critical Implementation Details

**Sygnatura (`reference`):** regex `ZW\.\d+\.\d+\.\d+\.\d+` — pierwsze trafienie w `NazwaZalacznika` dowolnego załącznika; brak dopasowania → `null` (fixture 932).

**Osoba fizyczna vs prawna:** nazwa z `OsobaPrawna/NazwaPodmiotu` lub sklejone `Imie` + `Nazwisko` (namespace osoby); `party_kind` z `Rodzaj`.

**CRD `delivery_event`:** stub zerowy (`status_code=0`, pozostałe pola null/0) — PDF CRD nie renderuje sekcji pocztowej „Zdarzenie doręczenia”; logika w `edelivery_receipt`.

**Golden — jeden kontrakt:** wszystkie 9 YAML muszą zawierać pełny zestaw kluczy Shipment/Recipient/EpoDocument; istniejące 6 dostają nowe pola jako `null` / `[]`.

## Phase 1: Model kanoniczny i korpus fixture

### Overview

Rozszerzyć typy domenowe i przygotować manifest + golden YAML (3 nowe + aktualizacja 6 istniejących) bez zmiany logiki parsera.

### Changes Required:

#### 1. Model domenowy

**File**: `domain/model.py`

**Intent**: Obsłużyć pola CRD w jednym `EpoDocument` / `Shipment` z domyślnymi wartościami dla starych fixture.

**Contract**: Nowe typy `Party`, `Attachment`, `EdeliveryReceipt`. `Recipient` + opcjonalne `edelivery_address`, `party_kind`. `Shipment` + opcjonalne `sender`, `attachments` (krotka), `edelivery_receipt`, `proof_id`. `EpoDocument` + opcjonalne `document_title`. Domyślne `None` / `()` tam, gdzie dotyczy.

#### 2. Manifest i README korpusu

**Files**: `tests/fixtures/manifest.yaml`, `tests/fixtures/README.md`

**Intent**: Zarejestrować 3 pliki CRD; udokumentować wariant `crd_potwierdzenie_otrzymania_v1`.

**Contract**: 3 wpisy (`crd-zw-856-2025`, `crd-zw-840-2025`, `crd-zw-932-2025`) ze `schema_variant: crd_potwierdzenie_otrzymania_v1`. Manifest == zbiór plików `*.xml` w katalogu.

#### 3. Golden YAML

**Files**: `tests/fixtures/expected/crd-zw-*.yaml` (3 nowe); aktualizacja 6 istniejących `expected/*.yaml`

**Intent**: Źródło prawdy dla parsera CRD i rozszerzonego kontraktu karta_epo.

**Contract**: Każdy `document` ma klucze `creation_date`, `document_title`, `shipments`. CRD: `document_title: "Potwierdzenie otrzymania"`, `creation_date: null`, wypełnione `sender`, `edelivery_receipt`, `attachments`, `proof_id`; karta_epo: nowe pola null/puste. Wartości pól CRD wyprowadzić z trzech plików XML (patrz Phase 1 manual verify).

#### 4. Testy korpusu i helperów

**Files**: `tests/test_fixture_corpus.py`, `tests/helpers.py`, `tests/conftest.py`

**Intent**: Walidacja kształtu golden i porównanie nowych pól w testach parametrizowanych.

**Contract**: `CRD_POTWIERDZENIE_NS` w conftest. `test_each_fixture_has_parseable_root` rozróżnia warianty po `schema_variant`. `_validate_document_shape` obejmuje nowe typy. `assert_document_matches_golden` porównuje `document_title`, `proof_id`, `sender`, `edelivery_receipt`, `attachments`.

### Success Criteria:

#### Automated Verification:

- `pytest tests/test_fixture_corpus.py -v` — struktura golden OK (parser może jeszcze padać do Phase 2)

#### Manual Verification:

- Ręczna weryfikacja wartości w `expected/crd-zw-856-2025.yaml` vs XML (nadawca RDL, adresat ANNA SYNTELOWA, daty, 2 załączniki)

**Implementation Note**: Po Phase 1 — potwierdzenie golden CRD przed implementacją parsera.

---

## Phase 2: Adapter CRD i rejestr parserów

### Overview

Implementacja `parse_crd_potwierdzenie`, dispatch `parse_epo_xml`, podpięcie pipeline.

### Changes Required:

#### 1. Adapter CRD

**File**: `parsers/crd_potwierdzenie_otrzymania.py`

**Intent**: Mapować `Dokument`/CRD 10856 na jeden `Shipment` z polami e-doręczeń.

**Contract**: `parse_crd_potwierdzenie(path: Path) -> EpoDocument`. `ParseError` dla złego root/namespace lub braku `TrescDokumentu`. XPath z namespace CRD + osoby. `has_outer_signature` = obecność `ds:Signature`. `tracking_number` ← `IdentyfikatorWiadomosci`. `proof_id` ← `IdentyfikatorDowoduPotwierdzenia`. Załączniki z `DaneZalaczniki` (`TrescWiadomosci == "Tak"` → `is_message_body: true`).

#### 2. Rejestr

**File**: `parsers/registry.py`

**Intent**: Jedno wejście parsowania dla pipeline i testów.

**Contract**: `parse_epo_xml(path) -> EpoDocument` — routuje `TabletKartaEpo`+KARTA_EPO_NS → `parse_pp_epo`, `Dokument`+CRD_NS → `parse_crd_potwierdzenie`; inaczej `ParseError` z komunikatem obu oczekiwanych formatów.

#### 3. Eksporty i pipeline

**Files**: `parsers/__init__.py`, `domain/pipeline.py`

**Intent**: Pipeline używa registry zamiast bezpośredniego PP parsera.

**Contract**: `convert_xml_file` woła `parse_epo_xml`. `__all__` zawiera `parse_epo_xml`, `parse_crd_potwierdzenie`, `ParseError`.

#### 4. Testy golden parsera

**File**: `tests/test_pp_epo_parser.py` (lub rename docstring na „parser golden”)

**Intent**: 9/9 manifest cases przez `parse_epo_xml`.

**Contract**: Parametryzacja bez skip; wszystkie id z manifestu.

### Success Criteria:

#### Automated Verification:

- `pytest tests/test_pp_epo_parser.py -v` — 9/9 green
- `pytest tests/test_fixture_corpus.py -v` — bez regresji

#### Manual Verification:

- `python -c "from parsers.registry import parse_epo_xml; ..."` na jednym pliku CRD — brak wyjątku

**Implementation Note**: Checkpoint przed PDF.

---

## Phase 3: PDF CRD i testy renderu

### Overview

Layout PDF dla dokumentów z `edelivery_receipt`; testy ekstrakcji tekstu.

### Changes Required:

#### 1. Renderer

**File**: `pdf/renderer.py`

**Intent**: Czytelny PDF dla CRD zgodny z FR-003 (nadawca, adresat, zdarzenia, załączniki).

**Contract**: Tytuł z `document.document_title` lub „Potwierdzenie otrzymania” gdy `edelivery_receipt`. Sekcje: Nadawca (`Party`), Adresat (Rodzaj, Nazwa, Adres e-Doręczeń), Identyfikatory wiadomości, Daty doręczenia, Załączniki (numerowana lista), Uwagi, stopka prawna. Gałąź pocztowa bez zmian dla `TabletKartaEpo`. Podpis: tekst o XAdES dla CRD, PKCS#7 dla karty EPO.

#### 2. Testy PDF

**File**: `tests/test_pdf_renderer.py`

**Intent**: Regresja layoutu CRD bez pikseli.

**Contract**: Co najmniej jeden test parametrizowany na `crd-zw-856-2025` — obecność „Potwierdzenie otrzymania”, „Nadawca”, „REGIONALNA DYREKCJA”, identyfikator wiadomości, załącznik z `ZW.224.1.856`. Istniejące testy karta_epo bez regresji.

### Success Criteria:

#### Automated Verification:

- `pytest tests/test_pdf_renderer.py -v` — all green

#### Manual Verification:

- Wizualny przegląd PDF z pliku 840 (3 załązniki, starostwo)

**Implementation Note**: Checkpoint przed fazą 4.

---

## Phase 4: Weryfikacja end-to-end

### Overview

CLI, batch mieszany, regresja S-01.

### Changes Required:

#### 1. Integracja (jeśli brakuje)

**Files**: `tests/test_integration_batch.py`, `tests/test_pipeline_batch.py` (opcjonalnie)

**Intent**: Batch z co najmniej jednym CRD w temp dir.

**Contract**: Jeden test: kopia CRD + karta EPO → 2× success w wynikach pipeline.

#### 2. Dokumentacja change

**File**: `context/changes/additional-xml-adapter/change.md`

**Intent**: Notatka o dostarczonym formacie i decyzjach planistycznych w `## Notes`.

### Success Criteria:

#### Automated Verification:

- `pytest -v` — full suite green

#### Manual Verification:

- `python main.py` w folderze z 1× CRD + 1× karta EPO → 2 PDF + `epo-konwersja.txt`
- Plik CRD 932: PDF bez sygnatury w sekcji identyfikatorów (`—`), bez błędu parsowania

---

## Testing Strategy

### Unit / golden:

- 9 przypadków `assert_document_matches_golden`
- Naming/summary bez zmian kontraktu — smoke po integracji

### Integration:

- Batch temp dir z CRD + karta EPO
- PDF text extraction dla CRD (pypdf)

### Manual:

1. Trzy pliki CRD z fixture — PDF + txt
2. Regresja `epo-jednostka-nadlesnictwo` — layout pocztowy nietknięty
3. Uszkodzony root XML — ten sam komunikat błędu co dziś, rozszerzony o CRD w tekście

## Performance Considerations

Pojedynczy plik CRD ~115 KB XML z podpisem — parse lxml + jeden PDF; bez budżetu poza S-01.

## Migration Notes

Brak migracji danych. Istniejące golden YAML wymagają jednorazowej aktualizacji kluczy — regresja parsera karta_epo musi pozostać zerowa po uzupełnieniu null.

## References

- Roadmap S-06: `context/foundation/roadmap.md`
- S-01 plan: `context/changes/single-xml-to-pdf-and-txt/plan.md`
- PRD FR-003, Business Logic: `context/foundation/prd.md`
- Fixture CRD: `tests/fixtures/ZW.224.1.856.2025 (Potwierdzenie otrzymania).xml`
- Model: `domain/model.py`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands.

### Phase 1: Model kanoniczny i korpus fixture

#### Automated

- [x] 1.1 `pytest tests/test_fixture_corpus.py -v` — struktura golden i manifest OK — aa83bdf

#### Manual

- [x] 1.2 Weryfikacja ręczna wartości `expected/crd-zw-856-2025.yaml` vs XML — aa83bdf

### Phase 2: Adapter CRD i rejestr parserów

#### Automated

- [x] 2.1 `pytest tests/test_pp_epo_parser.py -v` — 9/9 green — 792d470
- [x] 2.2 `pytest tests/test_fixture_corpus.py -v` — bez regresji — 792d470

#### Manual

- [x] 2.3 Import i parse jednego pliku CRD bez wyjątku — 792d470

### Phase 3: PDF CRD i testy renderu

#### Automated

- [ ] 3.1 `pytest tests/test_pdf_renderer.py -v` — all green

#### Manual

- [ ] 3.2 Wizualny przegląd PDF z fixture 840

### Phase 4: Weryfikacja end-to-end

#### Automated

- [ ] 4.1 `pytest -v` — full suite green

#### Manual

- [ ] 4.2 Batch CLI: 1× CRD + 1× karta EPO → 2 PDF + txt
- [ ] 4.3 Regresja layoutu karta EPO (jednostka nadleśnictwo)
