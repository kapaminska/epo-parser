# S-02: Exe w katalogu + partia XML — Plan Brief

> Full plan: `context/changes/directory-batch-run/plan.md`

## What & Why

Pracownik kancelarii uruchamia `epo-parser.exe` w folderze ze sprawą i oczekuje, że wszystkie pliki EPO XML w tym folderze staną się czytelnymi PDF-ami plus jednym plikiem `epo-konwersja.txt` z podsumowaniem. To gwiazda przewodnia produktu (roadmap S-02) — bez tego slice'a narzędzie pozostaje trybem deweloperskim „jeden plik z CLI”.

## Starting Point

S-01 dostarcza pełny pipeline pojedynczego pliku: parser → PDF → txt z sufiksami ` (2)`. `main.py` wymaga jednego argumentu; `format_summary` już obsługuje wiele wyników, ale CLI zawsze przekazuje listę jednoelementową. Brak skanu katalogu i trybu zero-argumentowego.

## Desired End State

Użytkownik double-clickuje exe w folderze z XML (lub wybiera wiele plików przez „Otwórz za pomocą”) i dostaje PDF obok każdego źródła oraz jedno podsumowanie txt. Przy pustym folderze — czytelny komunikat w txt. Przy częściowych błędach — widać który plik failnął; pozostałe PDF-y i tak powstają.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
|---|---|---|---|
| Skan katalogu | Płaski `*.xml` w cwd, bez rekursji | Zgodne z FR-001 i oczekiwaniem „folder sprawy” | Plan |
| Pusty folder | `epo-konwersja.txt` + komunikat PL, exit 1 | PRD guardrail — nie pusty wynik bez śladu | Plan |
| Błąd w partii | Continue-on-error; per-plik status w txt | Użytkownik musi wiedzieć który plik failnął; reszta się zapisuje | Plan |
| Exit code partii | 1 gdy jakikolwiek fail lub pusty skan | Spójne z S-01; sygnał dla skryptów/automatyzacji | Plan |
| Katalog podsumowania | cwd przy zero-arg; wspólny parent plików przy CLI paths | Double-click = cwd; Open-with = folder pliku | Plan |
| Wydajność 50/5 s | Smoke opcjonalny / manual, nie gate CI | NFR istnieje, ale test flaky cross-platform | Plan |

## Scope

**In scope:** `discover_xml_files`, `convert_xml_files`, refaktor `main.py` (zero-arg + multi-path), empty-batch txt, testy integracyjne batch, regresja S-01.

**Out of scope:** rekursja, folder-watcher, GUI, nowe adaptery XML, PyInstaller/CI Windows (S-05), twardy perf gate w CI.

## Architecture / Approach

```
argv (0..N paths)
    → [empty?] discover_xml_files(cwd)
    → convert_xml_files (loop convert_xml_file, continue on failure)
    → write_summary(summary_dir, results)
    → exit 0/1
```

Warstwa `domain/` dostaje discovery + batch loop; `main.py` tylko mapuje argv na ścieżki i katalog txt. Parser, PDF i naming bez zmian.

## Phases at a Glance

| Phase | What it delivers | Key risk |
|---|---|---|
| 1. Discovery + batch pipeline | `discover_xml_files`, `convert_xml_files`, empty summary | Sortowanie / edge case pustej listy |
| 2. CLI orchestration | Zero-arg, multi-path, exit codes | Regresja single-file S-01 |
| 3. Integration tests | Batch, empty, mixed, suffix tests | Subprocess cwd vs Open-with na Windows |

**Prerequisites:** S-01 complete (parser, PDF, naming, single-file CLI).
**Estimated effort:** ~1–2 sesje, 3 fazy.

## Open Risks & Assumptions

- Windows „Open-with” może ustawiać cwd inaczej niż katalog pliku — fallback CLI opiera się na jawnych ścieżkach, summary w `parent` pliku.
- Użytkownicy LP muszą uruchamiać exe **w** folderze sprawy (roadmap unknown) — komunikat empty-batch łagodzi pomyłkę.
- Test wydajności 50/5 s zależy od sprzętu; weryfikacja manualna przed release Windows.

## Success Criteria (Summary)

- Zero-arg w folderze z XML → wszystkie PDF + jeden txt.
- Folder bez XML → txt z komunikatem, exit 1.
- Partia mieszana → txt wskazuje failujące pliki, exit 1, sukcesy zapisane.
- `pytest -v` green, bez regresji testów S-01.
