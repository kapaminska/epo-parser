# S-01: Pojedynczy XML → PDF + txt — skrót planu

> Pełny plan: `context/changes/single-xml-to-pdf-and-txt/plan.md`
> Research: `context/changes/epo-fixture-corpus/plan.md` (F-01 — kontrakt kanoniczny i golden YAML)

## What & Why

Pierwszy działający przekrój produktu: jeden plik XML EPO z e-Doręczeń PP → czytelny PDF obok źródła + plik `epo-konwersja.txt`, bez nadpisywania istniejących wyjść. Ustanawia parser, renderer i reguły nazw, na których stoi S-02 (partia w katalogu).

## Starting Point

F-01 gotowy: `domain/model.py`, 6 fixture'ów + golden YAML, zielone testy strukturalne, pominięte testy parsera. Brak `parsers/`, `pdf/`, logiki nazw, prawdziwego `main.py`.

## Desired End State

`python main.py plik.xml` produkuje PDF z uwagami i stopką prawną oraz `epo-konwersja.txt`. Wszystkie 6 testów golden parsera i testy integracyjne (w tym ekstrakcja tekstu z PDF) przechodzą. Nierozpoznany XML → brak PDF, błąd w txt.

## Key Decisions Made

| Decyzja | Wybór | Dlaczego (1 zdanie) | Źródło |
| -------- | ----- | ------------------- | ------ |
| Orkiestracja S-01 | CLI jednego pliku + `epo-konwersja.txt` | Zgodność z outcome roadmap S-01 i ręczne testowanie | Plan |
| Stopka prawna | Minimalna stopka już w S-01 | PDF bez disclaimeru to ryzyko prawne; niski koszt fpdf2 | Plan |
| Błąd parsowania | Twardy błąd dla nierozpoznanego/uszkodzonego XML | Jasny sygnał złego pliku; rozpoznany EPO z lukami → PDF + uwagi | Plan |
| Testy PDF | Ekstrakcja tekstu (`pypdf`) | Wykrywa regresje layoutu bez porównywania pikseli | Plan |
| Nadawca w PDF | Brak sekcji | Pole nie występuje w fixture'ach / modelu (F-01) | Research |
| XAdES | Tylko flaga `has_outer_signature` | Pełna sekcja metadanych to S-04 | Research |
| Font | DejaVu osadzony w `pdf/assets/` | Polskie znaki — znane ryzyko fpdf2 | Plan |

## Scope

**W zakresie:**
- `parsers/pp_edoreczenia.py` + odklejenie skip w testach golden
- `domain/naming.py`, `domain/summary.py`, `domain/pipeline.py`
- `pdf/renderer.py` + font PL + stopka + sekcja uwag
- `main.py` — jedna ścieżka XML
- Testy: naming, summary, PDF text, integracja E2E

**Poza zakresem:**
- Skan katalogu / partia (S-02)
- Rozbudowana sekcja XAdES (S-04)
- Osobny slice stopki (S-03 — treść minimalna wchodzi tu)
- PyInstaller / CI (F-02)
- PDF/A, GUI, sieć, weryfikacja crypto

## Architecture / Approach

```
plik.xml ──► parsers/pp_edoreczenia ──► EpoDocument ──► pdf/renderer ──► .pdf
                              │                              │
                              └──────── warnings ────────────┘
                              │
main.py ──► domain/pipeline ──► domain/summary ──► epo-konwersja.txt
              │
              └── domain/naming (sufiksy (2), (3)…)
```

## Phases at a Glance

| Faza | Dostarcza | Główne ryzyko |
| ---- | --------- | ------------- |
| 1. Parser PP | `parse_pp_epo()` + 6 golden green | Namespace `DaneBiometryczne`; kolejność warnings |
| 2. Nazwy + txt | Sufiksy bez nadpisywania, format podsumowania | Edge case wielu kolizji `(N)` |
| 3. Renderer PDF | Layout PL, uwagi, stopka; testy pypdf | Font / diakrytyki |
| 4. CLI + E2E | `main.py`, integracja temp dir | Nazwa EZD ze spacjami |

**Wymagania wstępne:** F-01 zaimplementowany (tak)
**Szacunek:** ~3–4 sesje (4 fazy)

## Open Risks & Assumptions

- Variant B XSD PP — brak fixture'a; adapter może wymagać rozszerzenia bez zmian PDF.
- PDF/A nie potwierdzone z LP — fpdf2 standard PDF wystarczy na MVP.
- „Twardy błąd” nie dotyczy brakujących pól w rozpoznanym EPO — te idą przez warnings + PDF.

## Success Criteria (Summary)

- `pytest -v` green; 6 testów golden parsera bez skip.
- Jeden plik XML → PDF + txt obok źródła; kolizja → ` (2)` bez nadpisania.
- Nierozpoznany plik → brak PDF, czytelny wpis w `epo-konwersja.txt`.
