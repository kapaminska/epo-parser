# S-02: Exe w katalogu + partia XML — plan implementacji

## Overview

Rozszerzyć CLI o tryb partii zgodny z PRD FR-001/FR-002 i gwiazdą przewodnią roadmapy: użytkownik uruchamia `epo-parser.exe` dwuklikiem w folderze sprawy (zero argumentów) → program przetwarza wszystkie `*.xml` w bieżącym katalogu (bez rekursji), zapisuje PDF obok każdego źródła oraz jeden `epo-konwersja.txt` w katalogu roboczym. Fallback „Otwórz za pomocą” / wiele ścieżek CLI pozostaje — przetwarza wskazane pliki w jednej partii. S-01 dostarcza `convert_xml_file`, `format_summary`/`write_summary` i reguły sufiksów; ten slice dodaje odkrywanie plików, pętlę batch i nowy kontrakt `main.py`.

## Current State Analysis

S-01 jest zaimplementowany i zamknięty (`context/changes/single-xml-to-pdf-and-txt/plan.md` — wszystkie fazy `[x]`). `main.py` przyjmuje dokładnie jeden positional `xml_path`; brak skanu katalogu i trybu zero-arg. `domain/summary.py` już formatuje listę wyników (`Liczba plików: N`, blok per plik ze statusem/błędem/ostrzeżeniami). `domain/pipeline.py` eksponuje tylko `convert_xml_file`. Testy integracyjne (`tests/test_integration_single_xml.py`) pokrywają pojedynczy plik, sufiksy i błędy — brak testów batch / empty folder / zero-arg.

### Key Discoveries:

- `format_summary` + `test_format_summary_multiple_results` — warstwa txt gotowa na partię; brakuje komunikatu guardrail dla pustego skanu.
- `convert_xml_file` łapie `ParseError` wewnętrznie — pętla batch może kontynuować bez wyjątków.
- PRD guardrail: przy braku XML — jawny komunikat w `.txt`, nie pusty wynik (`prd.md` linia 41).
- Roadmap: oczekiwany tekst „brak plików XML” w podsumowaniu (`roadmap.md` linia 135).
- NFR: 50 plików / 5 s (`prd.md` linia 70) — weryfikacja manualna / opcjonalny test smoke, nie twardy gate CI na macOS.
- Decyzje planistyczne (sesja): skan płaski cwd; empty batch → txt + exit 1; continue-on-error; exit 1 gdy jakikolwiek plik failuje; per-plik status w txt obowiązkowy.

## Desired End State

Po zakończeniu S-02:

1. `python main.py` (zero argumentów) w folderze z plikami `.xml` przetwarza wszystkie XML w **tym** katalogu (bez podfolderów), tworzy PDF-y obok źródeł i `epo-konwersja.txt` w cwd.
2. `python main.py plik1.xml plik2.xml` — partia wskazanych plików; jedno podsumowanie txt.
3. Folder bez `.xml` przy zero-arg → `epo-konwersja.txt` z czytelnym komunikatem (np. „Brak plików XML w bieżącym katalogu.”), exit code `1`.
4. Partia mieszana (sukces + błąd parsowania) → wszystkie pliki przetworzone, txt identyfikuje który failnął, exit code `1`.
5. Drugie uruchomienie batch → sufiksy ` (2).pdf` / `epo-konwersja (2).txt` bez nadpisywania (bez regresji S-01).
6. Istniejące testy single-file green; nowe testy integracyjne batch green.

### Verification

```bash
pip install -e ".[dev]"
pytest -v
# w temp dir z kilkoma fixture'ami:
python main.py
python main.py file1.xml file2.xml
```

## What We're NOT Doing

- Rekursywny skan podfolderów.
- Folder-watcher / proces w tle (PRD Non-Goals).
- GUI, stderr jako kanał feedbacku — tylko PDF + txt.
- Nowe adaptery XML (S-06) ani zmiany renderera PDF (S-03/S-04).
- PyInstaller / CI Windows (F-02, S-05) — poza manualną weryfikacją „Open-with” na Windows LP przed zamknięciem slice'a.
- Twardy test wydajności 50/5 s w CI (flaky cross-platform); opcjonalny smoke lokalny.

## Implementation Approach

Trzy fazy: (1) odkrywanie + pipeline batch w `domain/`, (2) refaktor `main.py` z trzema trybami wejścia, (3) testy integracyjne. Logika biznesowa batch w `domain/`; `main.py` tylko orchestracja argv → discovery → `convert_xml_files` → `write_summary` → exit code. Zachować kompatybilność wsteczną: jeden plik jako jedyny argument działa jak S-01 (summary obok XML).

## Critical Implementation Details

**Tryby wejścia CLI:** (a) `argv` puste → `discover_xml_files(Path.cwd())`, summary w `Path.cwd()`; (b) jeden lub więcej argumentów → każdy traktowany jako ścieżka pliku (Open-with / fallback), summary w wspólnym katalogu rodzica gdy wszystkie pliki mają ten sam `parent`, w przeciwnym razie `Path.cwd()`.

**Continue-on-error:** pętla batch nigdy nie przerywa po pierwszym `status="failed"` — każdy plik ma wpis w txt z `Status: błąd` i `Błąd: …`.

**Exit code:** `0` tylko gdy co najmniej jeden plik przetworzony **i** wszystkie `status=="success"`; `1` gdy pusty skan, brak plików wejściowych, lub jakikolwiek błąd konwersji.

## Phase 1: Odkrywanie plików i pipeline batch

### Overview

Funkcje domenowe: flat scan `*.xml`, konwersja listy plików, format pustego podsumowania.

### Changes Required:

#### 1. Odkrywanie XML w katalogu

**File**: `domain/discovery.py`

**Intent**: Zwrócić deterministyczną listę plików EPO do przetworzenia w trybie exe-w-folderze.

**Contract**:

- `discover_xml_files(directory: Path) -> list[Path]`
- Tylko bezpośrednie dzieci katalogu: `directory.glob("*.xml")`, posortowane po `name` (case-sensitive na macOS/Linux; na Windows rozszerzenie `.xml` wystarczy zgodnie z PRD)
- Wyłącznie pliki (`is_file()`), bez rekursji
- Nie waliduje treści XML — to rola parsera

#### 2. Konwersja partii

**File**: `domain/pipeline.py`

**Intent**: Orkiestrować wiele plików bez zmiany kontraktu pojedynczego pliku.

**Contract**:

- `convert_xml_files(xml_paths: Iterable[Path]) -> list[ConversionResult]` — kolejność wyników = kolejność wejścia
- Dla każdej ścieżki wywołuje `convert_xml_file(path)`; wyjątki nieobsłużone poza `ParseError` nie powinny uciekać (parser już mapuje błędy na `ConversionResult`)
- Pusta lista wejściowa → pusta lista wyników (empty-batch obsługuje `main.py` + summary)

#### 3. Pusty skan w podsumowaniu

**File**: `domain/summary.py`

**Intent**: Spełnić PRD guardrail — jawny komunikat gdy brak XML w folderze.

**Contract**:

- Gdy `results` jest pusta lista, `format_summary` zwraca nagłówek + komunikat PL: `Brak plików XML w bieżącym katalogu.` (lub równoważny, spójny z roadmap risk note)
- Nie emitować `Liczba plików: 0` bez wyjaśnienia

#### 4. Testy jednostkowe discovery i batch pipeline

**File**: `tests/test_discovery.py`

**Intent**: Pokryć skan płaski, sortowanie, ignorowanie podfolderów.

**Contract**: Temp dir z `a.xml`, `b.xml`, podfolder `sub/nested.xml` → tylko `a.xml`, `b.xml` w kolejności alfabetycznej.

**File**: `tests/test_pipeline_batch.py`

**Contract**: Mock lub fixture — dwa pliki, jeden invalid → dwa `ConversionResult`, jeden failed; brak przerwania pętli.

#### 5. Pakiet wheel

**File**: `pyproject.toml`

**Intent**: Jeśli hatch wymaga jawnej listy — upewnić się, że nowy moduł jest pakowany (zwykle wystarczy import z `domain/`).

**Contract**: Brak regresji `packages = ["domain", "parsers", "pdf"]`.

### Success Criteria:

#### Automated Verification:

- `pytest tests/test_discovery.py tests/test_pipeline_batch.py -v` — all green
- `pytest tests/test_summary.py -v` — zaktualizowany test pustej listy

#### Manual Verification:

- Brak — czysta logika domenowa.

**Implementation Note**: Po tej fazie — krótkie potwierdzenie przed fazą 2.

---

## Phase 2: Orkiestracja CLI (`main.py`)

### Overview

Trzy tryby wejścia, agregacja wyników, jeden plik txt, spójne kody wyjścia.

### Changes Required:

#### 1. Refaktor entry point

**File**: `main.py`

**Intent**: Obsłużyć FR-001 (zero-arg batch) i FR-002 (wiele ścieżek) bez psucia S-01.

**Contract**:

- `argparse`: positional `paths`, `nargs="*"`, typ `Path`
- **Tryb A — zero arg:** `xml_paths = discover_xml_files(Path.cwd())`, `summary_dir = Path.cwd()`
- **Tryb B — jeden+ arg:** każdy element `paths` to plik; brakujący plik → `ConversionResult(failed, "Nie znaleziono pliku wejściowego.")` (jak S-01); `summary_dir = resolve_summary_directory(paths)`
- `resolve_summary_directory(paths: list[Path]) -> Path` — wspólny `parent` jeśli wszystkie resolved paths mają ten sam parent, else `Path.cwd()`
- Wywołanie: `results = convert_xml_files(xml_paths)` (lub lista wyników dla missing files przed/po konwersji)
- `write_summary(summary_dir, results)`
- **Exit code:** `1` jeśli `not results` (empty scan) LUB any `r.status == "failed"`; else `0`
- Docstring modułu zaktualizować — batch + single

#### 2. Test jednostkowy summary directory (opcjonalnie w test_main lub test_integration)

**File**: `tests/test_main_helpers.py` (lub inline w module testowym jeśli helpery wyciągnięte)

**Intent**: Stabilność reguły katalogu podsumowania.

**Contract**: Dwa pliki w tym samym folderze → summary w tym folderze; pliki z różnych folderów → `cwd`.

### Success Criteria:

#### Automated Verification:

- `pytest tests/test_integration_single_xml.py -v` — brak regresji S-01
- Import i `--help` działają

#### Manual Verification:

- `python main.py` w pustym katalogu → txt z komunikatem, exit 1
- `python main.py tests/fixtures/epo-odebrana-osobiscie.xml` — jak dotąd

**Implementation Note**: Po tej fazie — potwierdzenie manualne przed fazą 3.

---

## Phase 3: Testy integracyjne batch i weryfikacja wydajności

### Overview

Subprocess testy zero-arg i multi-file; dokumentacja manual Windows.

### Changes Required:

#### 1. Testy integracyjne partii

**File**: `tests/test_integration_batch.py`

**Intent**: End-to-end batch w temp dir przez subprocess (wzorzec `test_integration_single_xml.py`).

**Contract**:

- `_run_main(args: list[str], *, cwd: Path)` — opcjonalna lista argumentów po `main.py`
- **Batch zero-arg:** skopiować 2–3 fixture XML do temp dir → `python main.py` (bez args) → wszystkie PDF + jeden `epo-konwersja.txt` z `Liczba plików: N` i per-file status
- **Empty folder:** zero-arg w pustym dir → txt z „Brak plików XML”, exit 1, brak PDF
- **Mixed batch:** jeden valid + jeden pusty/invalid xml → jeden PDF, txt z jednym sukcesem i jednym błędem, exit 1
- **Multi-arg CLI:** `python main.py a.xml b.xml` — jak zero-arg dla tych plików
- **Suffix:** drugi batch run → `epo-konwersja (2).txt`
- **Non-regression:** podfolder z xml nie jest przetwarzany przy zero-arg (tylko pliki w root temp dir)

#### 2. Opcjonalny smoke wydajności (dev-only)

**File**: `tests/test_integration_batch.py` lub osobny test z `@pytest.mark.slow`

**Intent**: Orientacyjna kontrola NFR 50/5 s na maszynie deweloperskiej.

**Contract**: `@pytest.mark.skip` lub `slow` — skopiować ten sam fixture 50× z unikalnymi nazwami, zmierzyć czas `convert_xml_files`; nie failować domyślnego `pytest -v` na wolnych runnerach

#### 3. Aktualizacja testu summary pustej listy

**File**: `tests/test_summary.py`

**Contract**: Assert komunikatu guardrail w `format_summary([])`.

### Success Criteria:

#### Automated Verification:

- `pytest -v` — pełna suite green (bez slow jeśli domyślnie skip)
- `pytest tests/test_integration_batch.py -v`

#### Manual Verification:

- Uruchomienie `python main.py` w folderze z 6 fixture'ami — szybki przegląd txt
- (Przed zamknięciem slice'a) Windows LP: dwuklik exe w folderze sprawy + „Otwórz za pomocą” na pojedynczym XML — zgodnie z roadmap risk note

**Implementation Note**: Po tej fazie — końcowe potwierdzenie manualne; zaktualizować status S-02 w roadmap jeśli team prowadzi status ręcznie.

---

## Testing Strategy

### Unit Tests:

- `discover_xml_files` — flat, sort, ignore subdirs
- `convert_xml_files` — continue-on-error
- `format_summary([])` — guardrail message
- `resolve_summary_directory` — shared parent vs cwd

### Integration Tests:

- Zero-arg batch, empty dir, mixed results, multi-arg, suffix collision
- Regresja `test_integration_single_xml.py`

### Manual Testing Steps:

1. Folder z 3+ XML — zero-arg, sprawdź txt i PDF-y.
2. Folder bez XML — komunikat w txt.
3. Jeden dobry + jeden zły XML — oba wpisy w txt, exit 1.
4. (Windows) Dwuklik exe w folderze sprawy.
5. (Opcjonalnie) 50 kopii fixture — czas < 5 s lokalnie.

## Performance Considerations

NFR PRD: 50 PDF < 5 s. Batch to sekwencyjne wywołania `convert_xml_file` — wystarczające na MVP; brak równoległości. Font PDF ładowany per dokument (akceptowalne przy 50 plikach). Smoke test opcjonalny, nie blokuje CI.

## Migration Notes

Brak migracji danych. Użytkownicy S-01 CLI (`python main.py file.xml`) bez zmian behawioralnych. Zero-arg to nowy primary flow pod `.exe`.

## References

- S-01 plan: `context/changes/single-xml-to-pdf-and-txt/plan.md`
- PRD: `context/foundation/prd.md` (FR-001, FR-002, US-01, guardrails, NFR)
- Roadmap S-02: `context/foundation/roadmap.md`
- `main.py`, `domain/pipeline.py`, `domain/summary.py`
- `tests/test_integration_single_xml.py`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands.

### Phase 1: Odkrywanie plików i pipeline batch

#### Automated

- [x] 1.1 `pytest tests/test_discovery.py tests/test_pipeline_batch.py -v` — all green — 8f30a1e
- [x] 1.2 `pytest tests/test_summary.py -v` — test pustej listy — 8f30a1e

#### Manual

- [x] 1.3 (brak — przejście do fazy 2 po automated green) — 8f30a1e

### Phase 2: Orkiestracja CLI (`main.py`)

#### Automated

- [x] 2.1 `pytest tests/test_integration_single_xml.py -v` — brak regresji
- [x] 2.2 `--help` i import `main` działają

#### Manual

- [x] 2.3 Pusty katalog → txt + exit 1
- [x] 2.4 Pojedynczy plik CLI — zachowanie S-01

### Phase 3: Testy integracyjne batch i weryfikacja wydajności

#### Automated

- [ ] 3.1 `pytest -v` — full suite green
- [ ] 3.2 `pytest tests/test_integration_batch.py -v`

#### Manual

- [ ] 3.3 Batch 6 fixture'ów — przegląd txt
- [ ] 3.4 Windows LP: dwuklik + Open-with (przed zamknięciem slice'a)
