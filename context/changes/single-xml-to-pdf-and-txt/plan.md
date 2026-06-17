# S-01: Pojedynczy XML → PDF + podsumowanie txt — plan implementacji

## Overview

Zbudować pierwszy pionowy przekrój konwersji EPO: parser PP e-Doręczeń (`TabletKartaEpo` / `KartaEPO.xsd`) → model kanoniczny → PDF z sekcją uwag i stopką prawną → plik `epo-konwersja.txt`, z regułą sufiksów ` (2)` bez nadpisywania. Wejście: jedna ścieżka XML przez CLI (`python main.py plik.xml`). Slice ustanawia kontrakt adaptera dla przyszłych wariantów XSD (poziom A w roadmapie).

## Current State Analysis

F-01 (`epo-fixture-corpus`) jest zaimplementowany: `domain/model.py`, sześć fixture'ów XML, golden YAML, manifest, zielone testy strukturalne (`tests/test_fixture_corpus.py`). Testy parsera (`tests/test_pp_epo_parser.py`) są oznaczone `@pytest.mark.skip`. Brakuje `parsers/`, `pdf/`, logiki nazw wyjściowych, renderera PDF i prawdziwej orkiestracji — `main.py` to stub bootstrapowy.

### Key Discoveries:

- Kontrakt kanoniczny: `domain/model.py` — bez pola nadawca; `TabletJednostkaMS` → `PostalUnit`.
- Golden YAML + `tests/helpers.py` → `assert_document_matches_golden()` — kolejność `warnings` musi być deterministyczna.
- Namespace: `http://msepo.gov.pl/epo/XSD/KartaEPO.xsd`, root `TabletKartaEpo` (`tests/conftest.py`).
- `DaneBiometryczne` występuje bez prefiksu `mstns:` — parser musi tolerować mieszane namespace'y.
- Zewnętrzny blob `Podpis` → tylko flaga `has_outer_signature`; strukturalny XAdES to S-04.
- Stack: Python 3.14, `lxml`, `fpdf2`; pakiet wheel obecnie zawiera tylko `domain` (`pyproject.toml` linie 30–31).

## Desired End State

Po zakończeniu S-01:

1. `python main.py tests/fixtures/epo-odebrana-osobiscie.xml` w katalogu roboczym tworzy `epo-odebrana-osobiscie.pdf` i `epo-konwersja.txt` (lub wariant z sufiksem przy kolizji).
2. Wszystkie sześć testów golden parsera przechodzi bez skip.
3. Testy integracyjne w temp dir weryfikują nazewnictwo, format podsumowania i kluczowe wartości w tekście PDF.
4. Nierozpoznany lub uszkodzony XML → brak PDF, wpis błędu w `.txt`, kod wyjścia ≠ 0.
5. Rozpoznany EPO z brakującymi polami → PDF + ostrzeżenia w PDF i `.txt`.

### Verification

```bash
pip install -e ".[dev]"
pytest -v
python main.py tests/fixtures/epo-odebrana-osobiscie.xml
```

## What We're NOT Doing

- Skan katalogu i partia wielu plików (S-02: `directory-batch-run`).
- Rozbudowana sekcja metadanych XAdES (S-04) — tylko flaga obecności podpisu zewnętrznego.
- Osobny slice na stopkę prawną (S-03) — minimalna stopka wchodzi w S-01 zgodnie z decyzją planistyczną.
- Drugi wariant XSD PP bez fixture'a (Variant B TBD).
- Rejestr wielu adapterów źródeł (S-06) — w S-01 wystarczy detekcja + jeden adapter PP.
- PyInstaller / CI Windows (F-02, S-05).
- PDF/A — standardowy PDF fpdf2; PDF/A wymaga potwierdzenia z LP (`ai/idea.md` §8).
- GUI, sieć, weryfikacja kryptograficzna podpisu.

## Implementation Approach

Cztery fazy z ręcznym checkpointem po każdej (wzorzec F-01): parser → reguły wyjścia + txt → renderer PDF → CLI i integracja. Warstwy zgodnie z architekturą: `main` → `domain` ← `parsers`, `pdf`. Wyjątki parsowania (`ParseError`) żyją w `parsers/` lub cienkim `domain/errors.py`; `domain/` nie importuje `lxml` ani `fpdf2`.

## Critical Implementation Details

**Twardy błąd vs best-effort:** decyzja planistyczna „twardy błąd” dotyczy wyłącznie plików **nierozpoznanych** (zły root/namespace) lub **niewell-formed** XML. Rozpoznany `TabletKartaEpo` z pustymi polami → parser emituje `ParseWarning`, PDF powstaje — zgodnie z F-01 i PRD guardrail „generuj PDF, gdy to możliwe”.

**Font polski:** osadzić `DejaVuSans.ttf` (lub równoważny z pełnym PL) w `pdf/assets/` i zarejestrować w fpdf2 przed pierwszym `cell()` — Helvetica fpdf2 nie obsłuży „łąćęńóśźż”.

**EZD filename:** ścieżki wyłącznie przez `pathlib.Path`; test integracyjny musi obejmować fixture `Wiadomość EZD (...)(3).xml`.

## Phase 1: Parser PP e-Doręczeń

### Overview

Implementacja `parse_pp_epo()` mapującej XML na `EpoDocument` zgodnie z golden YAML; odklejenie skip w testach parametrizowanych.

### Changes Required:

#### 1. Pakiet parserów

**File**: `parsers/__init__.py`

**Intent**: Udostępnić publiczny punkt wejścia adaptera PP.

**Contract**: Re-export `parse_pp_epo` z `parsers.pp_edoreczenia`.

#### 2. Adapter PP

**File**: `parsers/pp_edoreczenia.py`

**Intent**: Wyodrębnić pola EPO z `TabletKartaEpo` do modelu kanonicznego; emitować ostrzeżenia dla brakujących pól zgodnie z golden YAML.

**Contract**:

- `parse_pp_epo(path: Path) -> EpoDocument`
- `ParseError(Exception)` — nie-well-formed XML lub root/namespace inny niż `TabletKartaEpo` + `KARTA_EPO_NS`
- Mapowanie elementów/atrybutów z fixture'ów (patrz `tests/fixtures/epo-*.xml`): `CreationDate`, `NumerNadania`, `DataNadania`, `Adresat`, adres, `Sygnatura`, `Rodzaj`, `StatusPrzesylki`, `BrakDoreczenia`, awizo, `Podpis` odbiorcy, `Wydajacy` (atrybuty), `TabletJednostkaMS` (opcjonalnie `None` gdy puste), zewnętrzny `Podpis` PKCS#7 → `has_outer_signature: bool`
- Puste `TabletJednostkaMS` (same puste tagi) → `postal_unit=None`
- Kody ostrzeżeń zgodne z golden: `missing_city`, `missing_reference`, `missing_operator` itd. — **kolejność emisji** zgodna z `expected_warnings` w YAML
- Tolerancja `DaneBiometryczne` bez prefiksu namespace (ignorować treść biometryczną w MVP)

#### 3. Konfiguracja pakietu

**File**: `pyproject.toml`

**Intent**: Dołączyć `parsers` do wheel.

**Contract**: `[tool.hatch.build.targets.wheel] packages = ["domain", "parsers"]`

#### 4. Testy golden

**File**: `tests/test_pp_epo_parser.py`

**Intent**: Włączyć testy parsera po implementacji.

**Contract**: Usunąć modułowe `pytestmark = pytest.mark.skip(...)`; wszystkie 6 przypadków z manifestu musi przejść.

### Success Criteria:

#### Automated Verification:

- `pytest tests/test_pp_epo_parser.py -v` — 6/6 green
- `pytest tests/test_fixture_corpus.py -v` — bez regresji
- `python -c "from parsers.pp_edoreczenia import parse_pp_epo"`

#### Manual Verification:

- Porównanie wizualne jednego wyniku parsera z `expected/epo-jednostka-nadlesnictwo.yaml` (pola Nadleśnictwa)

**Implementation Note**: Po tej fazie — potwierdzenie manualne przed fazą 2.

---

## Phase 2: Reguły nazw wyjściowych i podsumowanie txt

### Overview

Logika domenowa: bezpieczne nazwy PDF/txt z sufiksami ` (2)`, `(3)`… oraz format pliku `epo-konwersja.txt`.

### Changes Required:

#### 1. Reguły nazw plików

**File**: `domain/naming.py`

**Intent**: Centralna reguła PRD — nigdy nie nadpisuj istniejącego wyjścia.

**Contract**:

- `resolve_output_path(source: Path, extension: str, directory: Path | None = None) -> Path` — ten sam stem co XML, docelowe rozszerzenie (`.pdf`), katalog domyślnie obok źródła; jeśli docelowy plik istnieje, próbuj `stem (2).ext`, `stem (3).ext` … aż wolna ścieżka
- `resolve_summary_path(directory: Path) -> Path` — baza `epo-konwersja.txt`, ta sama reguła sufiksów
- Funkcje czyste, bez I/O poza sprawdzeniem `exists()`

#### 2. Model wyniku konwersji

**File**: `domain/conversion.py`

**Intent**: Typ wyniku pojedynczej konwersji dla orchestratora i writera txt.

**Contract**: `@dataclass` `ConversionResult` — pola: `source`, `pdf_path | None`, `status` (`success` | `failed`), `warnings: list[ParseWarning]`, `error_message: str | None`

#### 3. Writer podsumowania

**File**: `domain/summary.py`

**Intent**: Zapisać czytelne podsumowanie operacji dla użytkownika kancelarii.

**Contract**:

- `format_summary(results: list[ConversionResult]) -> str` — nagłówek PL, liczba plików, per plik: status, ścieżka PDF (lub „brak”), lista ostrzeżeń / komunikat błędu
- `write_summary(directory: Path, results: list[ConversionResult]) -> Path` — używa `resolve_summary_path`, zapis UTF-8

#### 4. Testy nazw i podsumowania

**File**: `tests/test_naming.py`

**Intent**: Obowiązkowe pokrycie reguły sufiksów (PRD guardrail).

**Contract**: Testy: brak kolizji → bazowa nazwa; istniejący `foo.pdf` → `foo (2).pdf`; analogicznie dla txt; trzecia kolizja → `(3)`.

**File**: `tests/test_summary.py`

**Contract**: Format txt zawiera nazwę źródła, status sukcesu/błędu i teksty ostrzeżeń.

### Success Criteria:

#### Automated Verification:

- `pytest tests/test_naming.py tests/test_summary.py -v` — all green

#### Manual Verification:

- Symulacja dwóch uruchomień na tym samym XML w temp dir — drugi run tworzy ` (2).pdf` i `epo-konwersja (2).txt`

**Implementation Note**: Po tej fazie — potwierdzenie manualne przed fazą 3.

---

## Phase 3: Renderer PDF

### Overview

Jeden renderer kanoniczny: stały układ sekcji, polskie znaki, uwagi, minimalna stopka prawna.

### Changes Required:

#### 1. Zasób fontu

**File**: `pdf/assets/DejaVuSans.ttf`

**Intent**: Pełny zestaw glifów polskich (ryzyko z `ai/idea.md` §8).

**Contract**: Font w repozytorium (DejaVu licencja OK); ścieżka względem modułu `pdf/`.

#### 2. Pakiet PDF

**File**: `pdf/__init__.py`

**Intent**: Publiczny eksport renderera.

**Contract**: Re-export `render_epo_pdf`.

#### 3. Renderer

**File**: `pdf/renderer.py`

**Intent**: Zamienić `EpoDocument` na czytelny PDF — bez znajomości XML.

**Contract**:

- `render_epo_pdf(document: EpoDocument, output_path: Path) -> None`
- Sekcje (nagłówki PL, stała kolejność): tytuł „Elektroniczne Potwierdzenie Odbioru”; **Adresat**; **Identyfikatory przesyłki** (numer, data nadania, sygnatura, rodzaj); **Zdarzenie doręczenia** (status, brak doręczenia, daty awizo, podpis odbiorcy); opcjonalnie **Jednostka** (`PostalUnit`); **Wydający** (`Operator`); **Uwagi / ostrzeżenia** (lista `ParseWarning.message`, lub „Brak uwag”); informacja o obecności zewnętrznego podpisu gdy `has_outer_signature`
- **Stopka prawna** (stały tekst, np.): „Niniejszy plik PDF stanowi wyłącznie wizualizację. Wiążącym dokumentem pozostaje oryginalny podpisany plik XML.”
- Puste pola → „—” lub pominięcie wiersza (spójnie w całym rendererze)
- Brak sekcji nadawca (brak w modelu)
- Parent katalog `output_path` musi istnieć lub być tworzony przez wywołującego

#### 4. Konfiguracja pakietu

**File**: `pyproject.toml`

**Contract**: `packages = ["domain", "parsers", "pdf"]`; opcjonalnie `[tool.hatch.build.targets.wheel.force-include]` dla `pdf/assets/*.ttf` jeśli hatch nie pakuje assets automatycznie.

#### 5. Dev dependency do testów PDF

**File**: `pyproject.toml`

**Intent**: Ekstrakcja tekstu z PDF w testach.

**Contract**: Dodać `pypdf>=5.0.0` do `[dependency-groups] dev`.

#### 6. Testy renderera

**File**: `tests/test_pdf_renderer.py`

**Intent**: Asercje na treści PDF bez porównywania pikseli.

**Contract**:

- Parametryzacja po manifeście (min. 2–3 reprezentatywne fixture'y + minimal z ostrzeżeniami)
- `render_epo_pdf(parse_pp_epo(xml), tmp_path / "out.pdf")` → ekstrakcja tekstu (`pypdf.PdfReader`) → assert zawiera `PUH7443447077999`, nagłówki sekcji, tekst stopki prawnej, komunikaty ostrzeżeń dla `epo-minimal-puste-pola`
- Assert polskich znaków (np. „ZIELIŃSKA”, „Piaseczno”)

### Success Criteria:

#### Automated Verification:

- `pytest tests/test_pdf_renderer.py -v` — all green
- `pip install -e ".[dev]"` z `pypdf`

#### Manual Verification:

- Jednorazowy wizualny przegląd wygenerowanego PDF z `epo-jednostka-nadlesnictwo.xml` (układ sekcji)

**Implementation Note**: Po tej fazie — potwierdzenie manualne przed fazą 4.

---

## Phase 4: Orkiestracja CLI i integracja end-to-end

### Overview

Połączenie parser → PDF → txt w `main.py`; pełny test integracyjny w temp dir.

### Changes Required:

#### 1. Pipeline konwersji

**File**: `domain/pipeline.py`

**Intent**: Jedna funkcja biznesowa dla pojedynczego pliku — używana przez CLI i testy.

**Contract**:

- `convert_xml_file(xml_path: Path, *, output_directory: Path | None = None) -> ConversionResult`
- Flow: `parse_pp_epo` → `resolve_output_path(..., ".pdf")` → `render_epo_pdf` → zbiór warnings; przy `ParseError` → `status=failed`, `pdf_path=None`, `error_message` po polsku
- `output_directory` domyślnie katalog źródłowego XML

#### 2. Entry point CLI

**File**: `main.py`

**Intent**: Minimalne uruchomienie S-01 — jedna ścieżka XML.

**Contract**:

- `argparse`: jeden positional `xml_path`
- Wywołanie `convert_xml_file` + `write_summary` w katalogu wyjściowym
- Kod wyjścia `0` gdy sukces, `1` gdy błąd parsowania / brak pliku wejściowego
- Komunikat błędu tylko w `.txt` (bez GUI) — zgodnie z PRD

**File**: `pyproject.toml`

**Contract**: `[project.scripts] epo-parser = "main:main"` (opcjonalnie, jeśli nie koliduje z `python main.py`)

#### 3. Test integracyjny

**File**: `tests/test_integration_single_xml.py`

**Intent**: End-to-end XML → PDF + txt w temp dir.

**Contract**:

- Kopia fixture do temp dir (w tym case z spacjami w nazwie EZD)
- Uruchomienie pipeline / subprocess `python main.py <path>`
- Assert: PDF istnieje, txt istnieje, txt zawiera nazwę XML i numer przesyłki
- Drugi run w tym samym dir → sufiks ` (2)` na PDF i txt
- Case: nie-XML / pusty plik → brak PDF, txt z błędem, exit code 1

### Success Criteria:

#### Automated Verification:

- `pytest -v` — wszystkie testy green (structural + parser + naming + summary + pdf + integration)
- `python main.py tests/fixtures/epo-odebrana-osobiscie.xml` — exit 0 w czystym temp dir

#### Manual Verification:

- Uruchomienie na macOS z fixture EZD (nazwa ze spacjami) — poprawne ścieżki wyjściowe
- Drugie uruchomienie — sufiksy bez nadpisania

**Implementation Note**: Po tej fazie — końcowe potwierdzenie manualne przed zamknięciem S-01.

---

## Testing Strategy

### Unit Tests:

- Parser golden (6 fixture'ów)
- `domain/naming.py` — sufiksy kolizji
- `domain/summary.py` — format txt
- `pdf/renderer.py` — ekstrakcja tekstu, PL diacritics, stopka, uwagi

### Integration Tests:

- `test_integration_single_xml.py` — pełny flow + kolizja nazw + błąd parsowania

### Manual Testing Steps:

1. Wygeneruj PDF z każdego z 6 fixture'ów — szybki przegląd układu.
2. Uruchom dwa razy na tym samym pliku — sprawdź ` (2).pdf` i `epo-konwersja (2).txt`.
3. Podaj plik `.txt` zamiast XML — brak PDF, czytelny błąd w podsumowaniu.

## Performance Considerations

Pojedynczy plik, <1 s na macOS — poza wymaganiami PRD (50 plików / 5 s dotyczy S-02). Font osadzony raz na dokument fpdf2.

## Migration Notes

Greenfield w warstwach aplikacji; F-01 bez zmian strukturalnych. Po S-01 zaktualizować `README.md` (usuwa przestarzałą informację „not bootstrapped”) — opcjonalnie w tej samej implementacji lub osobny commit.

## References

- F-01 plan: `context/changes/epo-fixture-corpus/plan.md`
- PRD: `context/foundation/prd.md` (FR-003, FR-004, Business Logic)
- Roadmap S-01: `context/foundation/roadmap.md`
- Design notes: `ai/idea.md` (§3.4, §4.3, §6)
- Model: `domain/model.py`
- Manifest: `tests/fixtures/manifest.yaml`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands.

### Phase 1: Parser PP e-Doręczeń

#### Automated

- [x] 1.1 `pytest tests/test_pp_epo_parser.py -v` — 6/6 green — bdf14a9
- [x] 1.2 `pytest tests/test_fixture_corpus.py -v` — bez regresji — bdf14a9
- [x] 1.3 Import `parse_pp_epo` działa — bdf14a9

#### Manual

- [x] 1.4 Pola Nadleśnictwa zgodne z golden dla `epo-jednostka-nadlesnictwo` — bdf14a9

### Phase 2: Reguły nazw wyjściowych i podsumowanie txt

#### Automated

- [x] 2.1 `pytest tests/test_naming.py tests/test_summary.py -v` — all green

#### Manual

- [x] 2.2 Drugi run w temp dir → ` (2).pdf` i `epo-konwersja (2).txt`

### Phase 3: Renderer PDF

#### Automated

- [ ] 3.1 `pytest tests/test_pdf_renderer.py -v` — all green
- [ ] 3.2 `pip install -e ".[dev]"` z `pypdf`

#### Manual

- [ ] 3.3 Wizualny przegląd PDF z `epo-jednostka-nadlesnictwo.xml`

### Phase 4: Orkiestracja CLI i integracja end-to-end

#### Automated

- [ ] 4.1 `pytest -v` — full suite green
- [ ] 4.2 `python main.py tests/fixtures/epo-odebrana-osobiscie.xml` — exit 0 w temp dir

#### Manual

- [ ] 4.3 Fixture EZD ze spacjami w nazwie — poprawne wyjścia
- [ ] 4.4 Nie-XML → brak PDF, błąd w txt, exit 1
