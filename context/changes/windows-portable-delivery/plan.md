# S-05: Windows portable delivery — plan implementacji

## Overview

Domknąć dostawę produktu: pojedynczy przenośny `epo-parser.exe` (PyInstaller one-file) na Windows 10/11 bez instalacji Pythona u użytkownika LP. Slice scala roadmap **F-02** (szkielet CI/build PyInstaller) i **S-05** (weryfikacja dostawy end-to-end), bo F-02 nie ma osobnego change foldera. S-02 (`directory-batch-run`) dostarcza zero-arg batch CLI — ten plan dodaje bundling zasobów, pipeline GitHub Actions na `windows-latest`, publikację artefaktu przez GitHub Releases oraz odroczoną weryfikację manualną Windows LP (S-02 §3.4).

## Current State Analysis

Aplikacja jest zaimplementowana: `main.py` obsługuje zero-arg (skan cwd), multi-path CLI, `epo-konwersja.txt`, PDF z sufiksami. Testy integracyjne uruchamiają `python main.py` — nie zbudowany `.exe`. Brak `.github/workflows/`, brak PyInstaller w zależnościach, brak `.spec`, brak obsługi `sys.frozen` / `sys._MEIPASS` dla fontu.

### Key Discoveries:

- `pdf/renderer.py:19` — `FONT_PATH` oparty o `Path(__file__).resolve().parent`; w one-file PyInstaller ścieżka się psuje bez `datas=` i resolvera frozen.
- `pyproject.toml:38-40` — `force-include` fontu w wheel; wzorzec do powtórzenia w `.spec` (`datas`).
- `pyproject.toml:10` — `requires-python >= 3.14`; CI musi używać Python 3.14 (`.python-version` = `3.14`).
- `directory-batch-run/change.md` — manual 3.4 (dwuklik + Open-with) odłożony do S-05.
- `tech-stack.md` — `deployment_target: github-releases`, `ci_provider: github-actions`, `packaging: pyinstaller`.
- `prd.md:72` — one-file, Windows 10/11, docelowo ≤ 80 MB; twardy limit po pierwszym buildzie (open question #1).
- Brak workflow = brak pomiaru rozmiaru `.exe` i brak artefaktu do testów LP.

## Desired End State

Po zakończeniu S-05:

1. Tag `v*` (np. `v0.1.0`) uruchamia workflow na `windows-latest`, który buduje `epo-parser.exe` (one-file) i publikuje go jako asset GitHub Release.
2. Workflow loguje rozmiar `.exe` w MB; wynik trafia do notatki w `context/changes/windows-portable-delivery/` i aktualizuje PRD open question #1 propozycją limitu.
3. Po buildzie CI uruchamia smoke: `epo-parser.exe` na fixture XML → PDF + `epo-konwersja.txt` w temp dir (exit 0).
4. Font DejaVu i zależności `lxml` działają w frozen runtime (polskie znaki w PDF).
5. Maintainer wykonuje checklistę manualną na Windows LP: dwuklik exe w folderze z XML, Open-with na pliku XML — oba scenariusze produkują PDF + txt.
6. `README.md` opisuje jak pobrać `.exe` i uruchomić w folderze sprawy.

### Verification

```bash
# lokalnie (macOS — tylko pytest; build wymaga Windows CI):
pip install -e ".[dev]"
pytest -v

# po tagu v0.1.0 — w GitHub Releases:
# pobierz epo-parser.exe → folder z fixture XML → dwuklik
# sprawdź PDF + epo-konwersja.txt
```

## What We're NOT Doing

- Instalator MSI / korporacyjny deployment (PRD Non-Goals).
- Code signing / Authenticode (brak wymogu MVP; możliwy follow-up).
- One-folder PyInstaller (PRD wymaga one-file).
- Automatyczne testy dwukliku / Open-with w CI (wymaga interakcji Windows shell).
- Twardy fail CI przy > 80 MB przed ustaleniem limitu z LP IT.
- macOS/Linux build artefaktów (tylko Windows `.exe`).
- Osobny change F-02 — scope wchodzi w ten plan (decyzja planistyczna: fold F-02 → S-05).

## Implementation Approach

Cztery fazy: (1) frozen runtime + spec, (2) CI build + smoke, (3) release + dokumentacja + pomiar rozmiaru, (4) akceptacja manualna Windows LP. Minimalna zmiana w warstwie PDF (`resource_path`); reszta to infra (`epo-parser.spec`, `.github/workflows/`, README). Testy aplikacyjne pozostają bez zmian — smoke exe to cienka warstwa w CI.

## Critical Implementation Details

**PyInstaller `add-data` separator:** W pliku `.spec` używaj `os.pathsep` (lub tuple w `Analysis.datas`), nie hardcoduj `;` vs `:` — spec musi być czytelny na macOS (dev) i poprawny na Windows (CI).

**Nazwa artefaktu:** `epo-parser.exe` — zgodnie z PRD (`epo-parser.exe` w folderze sprawy).

**Entry point:** `main.py` (console, bez `--windowed`). Zero-arg batch wymaga console subsystem — double-click otwiera okno konsoli na chwilę (akceptowalne per PRD; brak GUI).

**lxml:** Dołącz `hiddenimports` dla `lxml.etree` (i ewentualnie `lxml._elementpath` jeśli build failuje) — pierwszy build na CI ujawni brakujące importy.

## Phase 1: Frozen runtime i spec PyInstaller

### Overview

Przygotować aplikację i plik `.spec` tak, by one-file exe poprawnie ładował font i moduły Pythona.

### Changes Required:

#### 1. Resolver ścieżek zasobów

**File**: `pdf/resources.py` (nowy)

**Intent**: Jedna funkcja zwracająca absolutną ścieżkę pliku obok pakietu `pdf/`, działająca zarówno w dev (`__file__`), jak i w PyInstaller (`sys._MEIPASS`).

**Contract**:

- `def package_resource(relative: str) -> Path`
- Gdy `getattr(sys, "frozen", False)`: baza = `Path(sys._MEIPASS)`
- W przeciwnym razie: baza = `Path(__file__).resolve().parent`
- Zwraca `base / relative`

#### 2. Font w rendererze PDF

**File**: `pdf/renderer.py`

**Intent**: Użyć `package_resource("assets/DejaVuSans.ttf")` zamiast `Path(__file__).parent / "assets" / ...`.

**Contract**: `FONT_PATH = package_resource("assets/DejaVuSans.ttf")` — bez zmiany logiki renderowania.

#### 3. Plik spec PyInstaller

**File**: `epo-parser.spec` (nowy, w repo root)

**Intent**: Reprodukowalny one-file build z poprawnym bundlingiem pakietów i fontu.

**Contract**:

- `Analysis` entry: `main.py`
- `datas`: `("pdf/assets/DejaVuSans.ttf", "pdf/assets")` (format zgodny z PyInstaller / `os.pathsep`)
- `hiddenimports`: co najmniej `lxml.etree`
- `EXE`: `name="epo-parser"`, `console=True`, one-file (`exclude_binaries=False` + `COLLECT` lub standardowy one-file block)
- Output: `dist/epo-parser.exe` na Windows

#### 4. Zależność PyInstaller

**File**: `pyproject.toml`

**Intent**: PyInstaller dostępny w środowisku dev/CI bez osobnej instalacji ad hoc.

**Contract**: Dodaj `pyinstaller>=6.0` do `[project.optional-dependencies] dev` i `[dependency-groups] dev`.

#### 5. Test jednostkowy resolvera (dev mode)

**File**: `tests/test_pdf_resources.py` (nowy)

**Intent**: Potwierdzić, że w trybie nie-frozen ścieżka fontu istnieje i wskazuje na `pdf/assets/DejaVuSans.ttf`.

**Contract**: `package_resource("assets/DejaVuSans.ttf").is_file()` is True.

### Success Criteria:

#### Automated Verification:

- `pip install -e ".[dev]"` — instalacja z pyinstaller
- `pytest tests/test_pdf_resources.py -v` — green
- `pytest -v` — pełna regresja green (bez regresji renderera)

#### Manual Verification:

- (Opcjonalnie na maszynie Windows) `pyinstaller epo-parser.spec` → `dist/epo-parser.exe` uruchamia się na fixture XML

**Implementation Note**: Po fazie 1 i green pytest — można merge'ować resolver + spec przed CI; pełna weryfikacja exe następuje w fazie 2.

---

## Phase 2: CI build Windows (F-02)

### Overview

GitHub Actions: testy + build PyInstaller na `windows-latest`, artefakt workflow + smoke exe.

### Changes Required:

#### 1. Workflow testów (cross-platform / szybki gate)

**File**: `.github/workflows/ci.yml` (nowy)

**Intent**: Uruchamiać `pytest` na każdym push/PR — szybka informacja zwrotna bez Windows.

**Contract**:

- Trigger: `push`, `pull_request` na `main`
- Job `test`: `ubuntu-latest`, Python 3.14 (`actions/setup-python`), `pip install -e ".[dev]"`, `pytest -v`
- Bez build exe na Ubuntu (PyInstaller Windows-only dla `.exe`)

#### 2. Workflow build Windows

**File**: `.github/workflows/windows-build.yml` (nowy)

**Intent**: Na każdym push do `main` budować `.exe` i uploadować jako artifact; na tag `v*` — dodatkowo przygotować asset pod Release (faza 3).

**Contract**:

- Trigger: `push` branches `[main]`, `push` tags `v*`
- Runner: `windows-latest`, Python 3.14
- Steps: checkout → setup-python → `pip install -e ".[dev]"` → `pytest -v` → `pyinstaller epo-parser.spec --noconfirm`
- Upload artifact: `dist/epo-parser.exe`, retention 30 dni
- Step **Size report**: `Get-Item dist/epo-parser.exe | Select-Object Length` → log MB w output joba
- Step **Smoke test** (PowerShell):
  - `$tmpdir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_.FullName }`
  - Copy fixture `tests/fixtures/epo-jednostka-nadlesnictwo.xml` do `$tmpdir`
  - `& dist/epo-parser.exe` z `cwd=$tmpdir` (zero-arg — jeden xml w folderze)
  - Assert: exit 0, istnieje `*.pdf` i `epo-konwersja.txt`

#### 3. gitignore — bez zmian wymaganych

**File**: `.gitignore`

**Intent**: `dist/` i `build/` już ignorowane (linie 98–99) — potwierdzić brak commitu artefaktów build.

**Contract**: Brak zmian jeśli `dist/`, `build/` już na liście.

### Success Criteria:

#### Automated Verification:

- Push do brancha z workflow → job `windows-build` green na GitHub Actions
- Log joba zawiera rozmiar `.exe` w MB
- Smoke step green (PDF + txt)

#### Manual Verification:

- Pobranie artifact `epo-parser.exe` z runa workflow i uruchomienie lokalnie na Windows (poza CI)

**Implementation Note**: Pierwszy run może ujawnić brakujące `hiddenimports` — popraw `.spec` i re-run; nie merge'uj z czerwonym smoke.

---

## Phase 3: GitHub Release, dokumentacja i pomiar rozmiaru

### Overview

Opublikować `.exe` przez GitHub Releases; zaktualizować docs i PRD open question.

### Changes Required:

#### 1. Job release w workflow

**File**: `.github/workflows/windows-build.yml`

**Intent**: Przy tagu `v*` dołączyć `epo-parser.exe` do GitHub Release.

**Contract**:

- Warunek: `if: startsWith(github.ref, 'refs/tags/v')`
- Użyj `softprops/action-gh-release@v2` (lub `actions/upload-release-asset`) z plikiem `dist/epo-parser.exe`
- Release name / tag = ref tag; body: krótka instrukcja PL (skopiuj exe do folderu z XML, dwuklik)

#### 2. Notatka z pierwszym pomiarem

**File**: `context/changes/windows-portable-delivery/change.md` (sekcja Notes)

**Intent**: Zarchiwizować faktyczny rozmiar pierwszego buildu i propozycję limitu.

**Contract**: Po pierwszym green release — wpis: data, rozmiar MB, porównanie z celem 80 MB, rekomendacja limitu dla LP IT.

#### 3. Aktualizacja PRD open question

**File**: `context/foundation/prd.md`

**Intent**: Zamknąć open question #1 propozycją twardego limitu (nie blokuj implementacji jeśli LP nie odpowiedziało — wpisz „proposed: X MB, pending LP IT”).

**Contract**: Sekcja Open Questions #1 — dodaj measured size i proposed hard limit (np. measured + 10% headroom lub 80 MB jeśli poniżej).

#### 4. README użytkownika

**File**: `README.md`

**Intent**: Instrukcja dla pracownika LP i maintainera.

**Contract**:

- Usuń stale „not bootstrapped yet”
- Sekcja **Windows**: pobierz `epo-parser.exe` z GitHub Releases → skopiuj do folderu ze sprawą → dwuklik (lub Open-with na `.xml`)
- Sekcja **Developers**: `pip install -e ".[dev]"`, `pytest`, link do workflow build
- Wzmianka: brak Pythona u użytkownika końcowego

#### 5. AGENTS.md — opcjonalna jedna linia

**File**: `AGENTS.md`

**Intent**: Wskazać `epo-parser.spec` i workflow release dla agentów.

**Contract**: W sekcji Build — `pyinstaller epo-parser.spec` (Windows) / CI on tag.

### Success Criteria:

#### Automated Verification:

- Tag `v0.1.0` (lub kolejny semver) tworzy Release z assetem `epo-parser.exe`
- `README.md` nie zawiera „not bootstrapped yet”

#### Manual Verification:

- Pobranie exe **z Releases** (nie tylko artifact) i smoke na Windows

---

## Phase 4: Akceptacja Windows LP (S-02 deferred 3.4)

### Overview

Checklista manualna na stacji Windows 10/11 (docelowo LP); domknięcie odroczonej weryfikacji z S-02.

### Changes Required:

#### 1. Checklist w change notes

**File**: `context/changes/windows-portable-delivery/change.md`

**Intent**: Trwały zapis wyniku testów akceptacyjnych.

**Contract**: Sekcja `## Windows LP verification` z checkboxami i datą:

| Scenariusz | Kroki | Oczekiwany wynik | Pass |
|---|---|---|---|
| Dwuklik w folderze | Folder z 2+ fixture XML, exe obok, dwuklik | Wszystkie PDF + jeden `epo-konwersja.txt`, exit bez crash | |
| Open-with | PPM na `.xml` → Otwórz za pomocą → `epo-parser.exe` | PDF obok XML + txt w folderze pliku | |
| Pusty folder | Dwuklik exe w folderze bez XML | `epo-konwersja.txt` z komunikatem braku XML | |
| Polskie znaki | Fixture z diakrytykami / EZD ze spacjami | PDF czytelny, poprawne znaki PL | |

#### 2. Aktualizacja S-02 change (cross-ref)

**File**: `context/changes/directory-batch-run/change.md`

**Intent**: Zamknąć odłożony manual 3.4 z linkiem do wyniku S-05.

**Contract**: W Notes — „Manual 3.4 completed in S-05 (data)” lub „blocked: …” jeśli fail.

#### 3. Status change S-05

**File**: `context/changes/windows-portable-delivery/change.md` frontmatter

**Intent**: `status: implemented` po pass checklisty; `updated` = data weryfikacji.

**Contract**: Nie ustawiaj `implemented` bez co najmniej dwuklik + Open-with pass.

### Success Criteria:

#### Automated Verification:

- Brak (faza manualna)

#### Manual Verification:

- Wszystkie cztery wiersze checklisty PASS na Windows 10 lub 11
- Czas uruchomienia one-file (rozpakowanie) akceptowalny dla użytkownika biurowego (< ~10 s cold start — subiektywna ocena w Notes)

**Implementation Note**: Jeśli SmartScreen blokuje unsigned exe — udokumentuj obejście („Więcej informacji → Uruchom mimo to”); code signing poza scope.

---

## Testing Strategy

### Unit Tests:

- `tests/test_pdf_resources.py` — ścieżka fontu w dev mode
- Pełny `pytest -v` — regresja po każdej fazie

### Integration Tests:

- Istniejące testy `python main.py` — bez zmian; pokrywają logikę batch
- CI smoke exe (faza 2) — minimalna integracja frozen runtime

### Manual Testing Steps:

1. Pobierz `epo-parser.exe` z GitHub Release.
2. Skopiuj do folderu z `tests/fixtures/*.xml` (lub realnymi plikami LP).
3. Dwuklik — sprawdź PDF-y i `epo-konwersja.txt`.
4. Open-with na pojedynczym XML.
5. Folder pusty — sprawdź komunikat w txt.
6. Drugie uruchomienie — sufiksy ` (2)` bez nadpisania.

## Performance Considerations

- One-file PyInstaller: cold start obejmuje rozpakowanie do `%TEMP%` — akceptowalne per PRD NFR; nie optymalizuj UPX w MVP bez pomiaru (UPX może triggerować AV false positives).
- Smoke w CI: jeden plik XML wystarczy; nie uruchamiaj 50-file perf w CI.

## Migration Notes

Brak migracji danych. Użytkownicy przechodzą z `python main.py` (dev) na `epo-parser.exe` — ten sam folder roboczy i format wyjścia.

## References

- PRD NFR: `context/foundation/prd.md` (linia 72, open question #1)
- Tech stack: `context/foundation/tech-stack.md`
- S-02 plan: `context/changes/directory-batch-run/plan.md`
- Roadmap S-05 / F-02: `context/foundation/roadmap.md`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands.

### Phase 1: Frozen runtime i spec PyInstaller

#### Automated

- [x] 1.1 `pip install -e ".[dev]"` — pyinstaller w dev deps — 85e3bf3
- [x] 1.2 `pytest tests/test_pdf_resources.py -v` — green — 85e3bf3
- [x] 1.3 `pytest -v` — pełna regresja green — 85e3bf3

#### Manual

- [ ] 1.4 (Opcjonalnie Windows) lokalny `pyinstaller epo-parser.spec` → exe na fixture

### Phase 2: CI build Windows (F-02)

#### Automated

- [ ] 2.1 Push z workflow → job `windows-build` green
- [ ] 2.2 Log joba zawiera rozmiar `.exe` w MB
- [ ] 2.3 Smoke step — PDF + `epo-konwersja.txt`, exit 0

#### Manual

- [ ] 2.4 Pobranie artifact exe i uruchomienie poza CI

### Phase 3: GitHub Release, dokumentacja i pomiar rozmiaru

#### Automated

- [ ] 3.1 Tag `v*` tworzy Release z assetem `epo-parser.exe`
- [ ] 3.2 `README.md` zaktualizowany (bez stale bootstrap message)

#### Manual

- [ ] 3.3 Pobranie exe z Releases i smoke na Windows

### Phase 4: Akceptacja Windows LP (S-02 deferred 3.4)

#### Manual

- [ ] 4.1 Checklist: dwuklik w folderze z XML — PASS
- [ ] 4.2 Checklist: Open-with na `.xml` — PASS
- [ ] 4.3 Checklist: pusty folder — komunikat w txt — PASS
- [ ] 4.4 Checklist: polskie znaki w PDF — PASS
