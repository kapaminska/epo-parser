# S-05: Windows portable delivery — Plan Brief

> Full plan: `context/changes/windows-portable-delivery/plan.md`

## What & Why

Pracownik kancelarii LP musi uruchomić **jeden plik** `epo-parser.exe` w folderze ze sprawą — bez Pythona, instalatora i konfiguracji. S-05 domyka produkt end-to-end: PyInstaller one-file, CI na Windows, publikacja przez GitHub Releases oraz weryfikacja na Windows 10/11 (w tym odroczony dwuklik/Open-with z S-02).

## Starting Point

S-02 zaimplementowany: zero-arg batch, multi-path CLI, `epo-konwersja.txt`. Testy uruchamiają `python main.py`. Brak PyInstaller, `.spec`, workflow CI, obsługi frozen paths dla fontu DejaVu. F-02 (pyinstaller-windows-build) jest tylko w roadmap — bez change foldera.

## Desired End State

Tag `v*` buduje i publikuje `epo-parser.exe` na GitHub Releases. CI smoke potwierdza konwersję fixture → PDF + txt. Maintainer dokumentuje rozmiar exe i proponuje twardy limit MB w PRD. Checklista LP na Windows: dwuklik, Open-with, pusty folder, polskie znaki — wszystko PASS.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
|---|---|---|---|
| F-02 scope | Fold into S-05 | Brak osobnego change F-02; jeden plan domyka CI + delivery | Plan |
| Distribution | GitHub Releases on `v*` tag | Zgodne z tech-stack `github-releases`; kanoniczny URL dla LP | Plan |
| Exe size gate | Measure + log; no hard fail yet | PRD: twardy limit po pierwszym buildzie; unikamy blokady na tuning | Plan |
| PyInstaller mode | One-file, console | PRD NFR; zero-arg batch wymaga console subsystem | Plan |
| Frozen font | `package_resource()` + `datas` in spec | `__file__` łamie się w one-file bez tego | Plan |
| Windows verify | CI smoke + manual LP checklist | Smoke łapie bundling; dwuklik/Open-with tylko manual | Plan |
| Code signing | Out of scope MVP | Unsigned exe OK z dokumentacją SmartScreen | Plan |

## Scope

**In scope:** `pdf/resources.py`, update `renderer.py`, `epo-parser.spec`, pyinstaller dev dep, `.github/workflows/ci.yml` + `windows-build.yml`, GitHub Release asset, README, PRD size note, Windows LP checklist, S-02 manual 3.4 closure.

**Out of scope:** MSI, code signing, one-folder build, macOS/Linux exe, automated double-click tests, hard 80 MB CI fail before LP IT decision, UPX/AV tuning beyond first green build.

## Architecture / Approach

```
main.py + domain/ + parsers/ + pdf/
        │
        ▼
epo-parser.spec (one-file, datas=font, hiddenimports=lxml)
        │
        ▼
GitHub Actions windows-latest → dist/epo-parser.exe
        │
        ├── artifact (every main push)
        ├── smoke: exe on fixture → PDF + txt
        └── GitHub Release (tag v*)
```

## Phases at a Glance

| Phase | What it delivers | Key risk |
|---|---|---|
| 1. Frozen runtime + spec | Font path works in frozen exe; committed `.spec` | Missing lxml hiddenimports |
| 2. CI build (F-02) | `windows-build.yml`, size log, exe smoke | First Windows build surprises |
| 3. Release + docs | GH Release, README, PRD size proposal | Tag discipline / permissions |
| 4. Windows LP acceptance | Manual checklist; close S-02 3.4 | SmartScreen on unsigned exe |

**Prerequisites:** S-02 implemented (yes); repo on GitHub with Actions enabled.
**Estimated effort:** ~2–3 sessions, 4 phases.

## Open Risks & Assumptions

- Pierwszy build może wymagać iteracji `hiddenimports` w `.spec` (lxml, fpdf2).
- Unsigned exe — SmartScreen może wymagać „Uruchom mimo to”; udokumentować, nie blokować MVP.
- Python 3.14 na `windows-latest` — verify availability in setup-python; fallback pin if runner lags.
- Rozmiar exe może przekroczyć 80 MB — log + PRD update, tuning w follow-up if needed.
- Użytkownik LP musi uruchamiać exe **w** folderze sprawy (S-02 assumption).

## Success Criteria (Summary)

- Tag release → pobieralny `epo-parser.exe` bez Pythona u użytkownika.
- CI smoke: fixture → PDF + `epo-konwersja.txt` via exe.
- Manual Windows: dwuklik batch + Open-with — PASS.
- Rozmiar exe zmierzony i zapisany; PRD open question #1 zaktualizowany propozycją limitu.
