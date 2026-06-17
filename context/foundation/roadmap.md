---
project: "EPO Parser"
version: 3
status: draft
created: 2026-06-17
updated: 2026-06-17
prd_version: 2
main_goal: quality
top_blocker: skills
---

# Roadmap: EPO Parser

> Derived from `context/foundation/prd.md` (v2). Edit-in-place; archive when superseded.
> Slices below are listed in dependency order. The "At a glance" table is the index.

## Vision recap

Pracownicy kancelarii w Lasach Państwowych otrzymują EPO z e-Doręczeń Poczty Polskiej jako surowy XML. EPO Parser to proste, w 100% offline narzędzie: użytkownik uruchamia `epo-parser.exe` w folderze z XML, dostaje PDF obok źródeł oraz plik `epo-konwersja.txt` z podsumowaniem — bez okienka GUI.

## North star

**S-02: Exe w katalogu + partia XML** — user can run the exe in a folder to convert all XML files and receive a numbered text summary.

> Gwiazda przewodnia — najmniejsza historyjka end-to-end, której udana realizacja dowodzi, że produkt działa dla pracownika kancelarii: uruchom `.exe` w folderze sprawy → PDF-y + `epo-konwersja.txt`. Wymaga działającego rdzenia z `S-01` (pojedynczy plik, PDF, txt).

## Extensibility

Architektura celowo oddziela format wejściowy od wizualizacji. PRD §Business Logic wymaga mapowania XML → **model kanoniczny** → PDF, niezależnie od wariantu XSD; PRD §Non-Goals wyklucza inne standardy z MVP, ale zostawia architekturę otwartą.

**Dwa poziomy dokładania formatów:**

| Poziom | Przykład | Co robisz | Warstwy dotknięte |
|---|---|---|---|
| **A — wariant XSD tego samego źródła** | Kolejny schemat EPO e-Doręczeń PP | Nowy moduł w `parsers/` + fixture + testy | `parsers/` (+ ewentualnie drobne rozszerzenie `domain/`) |
| **B — nowe źródło / standard** | ePUAP UPO, inny nadawca XML | Ten sam wzorzec co poziom A; aktywuj **`S-06`** per źródło | `parsers/`; `pdf/` i plik `.txt` **bez zmian**, o ile model kanoniczny wystarcza |

**Niezmienny pipeline:**

```
XML (format A) ──► parsers/ ──► domain/ (model kanoniczny) ──► pdf/ ──► PDF
XML (format B) ──► parsers/ ──┘                              └── main.py → epo-konwersja.txt
```

**Kontrakt na MVP (`S-01`):** pierwszy parser + rejestr/wybór adaptera, żeby poziom A nie wymagał przeróbek PDF ani formatu podsumowania. **Po MVP:** każde nowe źródło (poziom B) = osobna instancja **`S-06`** (własny `change-id`, np. `epuap-upo-adapter`).

## At a glance

| ID | Change ID | Outcome (user can …) | Prerequisites | PRD refs | Status |
|---|---|---|---|---|---|
| F-01 | epo-fixture-corpus | (foundation) reprezentatywne próbki XML EPO i ścieżka weryfikacji ekstrakcji modelu kanonicznego | — | Business Logic | ready |
| F-02 | pyinstaller-windows-build | (foundation) szkielet CI/build PyInstaller pod przenośny `.exe` Windows | — | NFR (Windows, portable) | done |
| S-01 | single-xml-to-pdf-and-txt | convert one XML file to PDF with warnings, non-destructive PDF/txt naming, and a text summary file | F-01 | US-01, FR-003, FR-004 | blocked |
| S-02 | directory-batch-run | run exe in a folder to process all XML (batch) with Open-with CLI fallback | S-01 | US-01, FR-001, FR-002 | proposed |
| S-03 | pdf-legal-footer | see a legal visualization footer in the PDF stating XML remains binding | S-01 | FR-005 | proposed |
| S-04 | xades-metadata-section | see optional XAdES signature metadata as a PDF section (no crypto verification) | S-01 | FR-006 | proposed |
| S-05 | windows-portable-delivery | run a single portable `.exe` on Windows 10/11 without Python installed | S-02, F-02 | NFR (Windows, portable, size) | proposed |
| S-06 | additional-xml-adapter | convert XML from an additional registered source into the same canonical PDF layout | S-01 | Business Logic, Non-Goals | proposed |

## Streams

Navigation aid — groups items that share a Prerequisites chain. Canonical ordering still lives in the dependency graph below.

| Stream | Theme | Chain | Note |
|---|---|---|---|
| A | Rdzeń konwersji | `F-01` → `S-01` → `S-02` | Jakość: parser/PDF/txt przed skanem katalogu (gwiazda przewodnia). |
| B | Rozszerzenia PDF | `S-03` / `S-04` | Równolegle po `S-01`; nice-to-have FR. |
| C | Dostawa Windows | `F-02` → `S-05` | Dołącza po `S-02`; PyInstaller na `windows-latest`. |
| D | Kolejne formaty XML | `S-06` (×N po MVP) | Post-MVP; wymaga tylko `S-01`. |

## Baseline

Stan kodu na `2026-06-17`. Brak implementacji — tylko dokumentacja foundation i reguły Cursor.

- **Aplikacja Python:** absent — `parsers/`, `domain/`, `pdf/`, `main.py` do zbudowania wg tech-stack.md.
- **Data:** absent — wyłącznie I/O plików (PDF + txt w katalogu roboczym).
- **Auth:** per tech-stack.md — brak auth (single user, offline).
- **Deploy / infra:** absent — brak `.github/workflows/`; F-02 dostarczy PyInstaller CI.
- **Observability:** absent — feedback przez `epo-konwersja.txt` i sekcję uwag w PDF (nie osobny system logów).

## Foundations

### F-01: Korpus próbek XML EPO

- **Outcome:** (foundation) reprezentatywne próbki XML EPO i ścieżka weryfikacji ekstrakcji modelu kanonicznego są dostępne do pracy nad parserem.
- **Change ID:** epo-fixture-corpus
- **PRD refs:** Business Logic (mapowanie wariantów XSD → model kanoniczny)
- **Unlocks:** `S-01`, wzorzec testów adapterów (§ Extensibility poziom A); redukuje ryzyko `skills`
- **Prerequisites:** —
- **Parallel with:** F-02
- **Blockers:** —
- **Unknowns:**
  - Jakie warianty XSD EPO występują w danych produkcyjnych Lasów Państwowych? — Owner: user. Block: no.
- **Risk:** Bez fixture'ów parser planuje się w próżni; foundation minimalizuje to ryzyko bez budowania całej warstwy domenowej z góry.
- **Status:** ready

### F-02: Build PyInstaller Windows

- **Outcome:** (foundation) szkielet CI na `windows-latest` produkuje one-file `.exe` PyInstaller bez ręcznej konfiguracji od zera.
- **Change ID:** pyinstaller-windows-build
- **PRD refs:** NFR (pojedynczy `.exe`, Windows 10/11, brak pre-instalacji Pythona)
- **Unlocks:** `S-05`; pomiar rozmiaru artefaktu pod limit MB z PRD
- **Prerequisites:** —
- **Parallel with:** F-01, S-03, S-04 (po `S-01`)
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Pierwszy build ujawnia realny rozmiar `.exe`; wynik zapisuj w PRD Open Question #1.
- **Status:** done

## Slices

### S-01: Pojedynczy XML → PDF + podsumowanie txt

- **Outcome:** user can convert one XML file to a readable PDF with embedded warnings, non-destructive PDF naming (` (2).pdf`), and a text summary file (`epo-konwersja.txt` with `(2)` suffix on conflict).
- **Change ID:** single-xml-to-pdf-and-txt
- **PRD refs:** US-01, FR-003, FR-004
- **Prerequisites:** F-01
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:**
  - Czy masz reprezentatywne pliki XML EPO (w tym „trudne” warianty XSD) do weryfikacji parsera i PDF? — Owner: user. Block: yes.
- **Risk:** Największe ryzyko (`skills`) — XML → model kanoniczny → PDF + txt; musi ustanowić kontrakt adaptera (§ Extensibility).
- **Status:** blocked

### S-02: Exe w katalogu + partia XML

- **Outcome:** user can run the exe in a folder to process all `.xml` in the current directory (batch), with Open-with / CLI path fallback for files outside the folder.
- **Change ID:** directory-batch-run
- **PRD refs:** US-01, FR-001, FR-002
- **Prerequisites:** S-01
- **Parallel with:** S-03, S-04, S-06
- **Blockers:** —
- **Unknowns:**
  - Czy użytkownik LP rozumie, że `.exe` trzeba uruchomić w folderze ze sprawą (nie skrótem z innego miejsca)? — Owner: user. Block: no.
- **Risk:** Zły katalog roboczy → jawne podsumowanie w `.txt` („brak plików XML”); weryfikacja na Windows LP przed zamknięciem slice'a.
- **Status:** proposed

### S-03: Stopka prawna w PDF

- **Outcome:** user can see a legal visualization footer in the PDF stating XML remains the binding document.
- **Change ID:** pdf-legal-footer
- **PRD refs:** FR-005
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-04, S-06, F-02
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Nice-to-have; bezpieczne do odłożenia bez blokowania MVP.
- **Status:** proposed

### S-04: Sekcja metadanych XAdES

- **Outcome:** user can see optional XAdES signature metadata as a PDF section without cryptographic verification.
- **Change ID:** xades-metadata-section
- **PRD refs:** FR-006
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-03, S-06, F-02
- **Blockers:** —
- **Unknowns:**
  - W jakiej formie metadane XAdES występują w realnych plikach EPO LP? — Owner: user. Block: no.
- **Risk:** Ekstrakcja bez weryfikacji crypto zgodna z Non-Goals; kształt danych może wymagać iteracji po fixture'ach.
- **Status:** proposed

### S-05: Dostawa przenośnego `.exe`

- **Outcome:** user can run a single portable `.exe` on Windows 10/11 without installing Python.
- **Change ID:** windows-portable-delivery
- **PRD refs:** NFR (Windows, portable, rozmiar ≤ 80 MB docelowo)
- **Prerequisites:** S-02, F-02
- **Parallel with:** S-03, S-04, S-06
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Domyka dostawę; wymaga działającej gwiazdy przewodniej (`S-02`) i pipeline'u (`F-02`).
- **Status:** proposed

### S-06: Adapter kolejnego źródła XML *(post-MVP, szablon)*

- **Outcome:** user can convert XML from an additional registered source into the same canonical PDF layout and text summary format.
- **Change ID:** additional-xml-adapter *(przy planowaniu: własny kebab-case, np. `epuap-upo-adapter`)*
- **PRD refs:** Business Logic, Non-Goals (architektura otwarta)
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-03, S-04, S-05
- **Blockers:** —
- **Unknowns:**
  - Które źródło / standard XML dodać jako następne? — Owner: user. Block: yes.
  - Czy model kanoniczny wymaga rozszerzenia? — Owner: team. Block: yes (jeśli tak — slice na `domain/` przed adapterem).
- **Risk:** Aktywuj po domknięciu MVP (`S-02`+). Zakres: `parsers/` + fixture + testy; bez przeróbek `pdf/` i formatu `.txt`.
- **Status:** proposed

## Backlog Handoff

| Roadmap ID | Change ID | Suggested issue title | Ready for `/10x-plan` | Notes |
|---|---|---|---|---|
| F-01 | epo-fixture-corpus | Korpus próbek XML EPO i ścieżka weryfikacji modelu | yes | Odblokowuje `S-01` |
| F-02 | pyinstaller-windows-build | CI PyInstaller → one-file `.exe` Windows | yes | Równolegle z F-01 |
| S-01 | single-xml-to-pdf-and-txt | XML → PDF + epo-konwersja.txt | no | Wymaga F-01 + plików XML (Unknown Block: yes) |
| S-02 | directory-batch-run | Exe w katalogu + partia + fallback CLI | no | Gwiazda przewodnia; wymaga `S-01` |
| S-03 | pdf-legal-footer | Stopka prawna w PDF | no | Nice-to-have |
| S-04 | xades-metadata-section | Sekcja metadanych XAdES w PDF | no | Nice-to-have |
| S-05 | windows-portable-delivery | Przenośny `.exe` bez Pythona u użytkownika | no | Wymaga `S-02` i `F-02` |
| S-06 | additional-xml-adapter | Adapter kolejnego źródła XML (szablon) | no | Post-MVP |

## Open Roadmap Questions

1. **Jakie warianty XSD EPO występują w danych produkcyjnych Lasów Państwowych?** — Owner: user. Block: `F-01`, `S-01`.
2. **Jaki twardy limit rozmiaru `.exe` po pierwszym buildzie PyInstaller?** — Owner: user / IT LP. Block: `S-05`.
3. **Które źródło XML (poza e-Doręczeniami PP) ma pierwszeństwo po MVP?** — Owner: user. Block: `S-06`.

## Parked

- **Weryfikacja kryptograficzna podpisów XAdES/CAdES** — Why parked: PRD §Non-Goals.
- **Folder-watcher / proces w tle** — Why parked: PRD §Non-Goals.
- **Instalatory korporacyjne (MSI)** — Why parked: PRD §Non-Goals.
- **Konkretne adaptery pod inne standardy (np. ePUAP UPO)** — Why parked: MVP; realizacja przez **`S-06`**. Warianty XSD PP → poziom A w `parsers/`.

## Done

- **F-02: (foundation) szkielet CI na `windows-latest` produkuje one-file `.exe` PyInstaller bez ręcznej konfiguracji od zera.** — Archived 2026-06-17 → `context/archive/2026-06-17-pyinstaller-windows-build/`. Lesson: —.
