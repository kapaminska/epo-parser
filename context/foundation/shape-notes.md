---
project: "EPO Parser"
context_type: greenfield
product_type: desktop
target_scale:
  users: small
  qps: null
  data_volume: small
timeline_budget:
  mvp_weeks: 1
  hard_deadline: null
  after_hours_only: true
created: 2026-06-17
updated: 2026-06-17
checkpoint:
  current_phase: 8
  phases_completed: [1, 2, 3, 4, 5, 6, 7]
  gray_areas_resolved:
    - topic: "Pain category"
      decision: "Data trapped somewhere (XML requires parsing)"
    - topic: "Insight"
      decision: "Poczta Polska nie dostarcza przyjaznego wariantu EPO w standardzie."
    - topic: "Persona scope"
      decision: "A specific role inside an org (pracownik kancelarii w Lasach Państwowych)"
  frs_drafted: 6
  quality_check_status: accepted
---

> **Rola tego pliku:** zapis z fazy `/10x-shape` — kontekst odkrycia i wczesne FR. **Aktualne decyzje produktowe i stack:** `prd.md` (v2) + `tech-stack.md` + `roadmap.md`. Gdzie poniżej widać GUI lub inny UX, obowiązuje PRD v2 (exe w katalogu + `epo-konwersja.txt`).

## Vision & Problem Statement

Pracownicy administracyjni / kancelarii w Lasach Państwowych otrzymują Elektroniczne Potwierdzenia Odbioru (EPO) z e-Doręczeń Poczty Polskiej w surowym formacie XML, co powoduje, że dane są "uwięzione" – brakuje możliwości łatwego odczytania i zarchiwizowania wizualizacji dokumentu. Kosztuje ich to utrudnione procesowanie spraw i brak czytelnego archiwum.

Zauważyliśmy, że Poczta Polska nie dostarcza przyjaznego, czytelnego wariantu EPO (np. PDF) w standardzie, co tworzy lukę, którą to proste narzędzie offline idealnie wypełnia.

## User & Persona

Pracownik administracji / kancelarii w Lasach Państwowych. Osoba nietechniczna, która na co dzień obsługuje przesyłki i potrzebuje niezawodnie, szybko zamienić plik XML na czytelny PDF do wpięcia do akt.

## Access Control

Single user; no auth; data lives on-device only. (Narzędzie desktopowe uruchamiana na żądanie bez rejestracji i logowania).

## Success Criteria

### Primary
1. Użytkownik uruchamia program dwuklikiem lub przeciąga na niego plik(i) XML.
2. Aplikacja generuje czytelne pliki PDF obok źródeł z tą samą nazwą bazową.
3. Aplikacja wyświetla podsumowanie w małym oknie GUI z informacją o statusie i ostrzeżeniach.

### Secondary
- Czytelne sekcje z uwagami / brakami w samym dokumencie PDF, w razie problemów z parsowaniem pliku XML.
- Nigdy nie nadpisujemy istniejącego pliku (przy konflikcie dokłada sufiks, np. `epo_123 (2).pdf`).

### Guardrails
- Aplikacja zawsze wygeneruje PDF, jeśli to tylko możliwe; nigdy nie wysypuje się po cichu (no silent crashes).
- Pozostaje pojedynczym plikiem wykonywalnym (.exe) i nie wymaga instalacji, konfiguracji folderów w tle czy uprawnień admina.

## Functional Requirements

### Przetwarzanie i Interfejs
- FR-001: Użytkownik może przekazać plik XML do programu metodą przeciągnij-i-upuść lub "Otwórz za pomocą". Priority: must-have
  > Socrates: Counter-argument considered: "Nie wszystkie konfiguracje Windows pozwalają na przeciąganie na .exe". Resolution: Kept, but ensure "Otwórz za pomocą" (i otwieranie z parametrem ścieżki) działa bezbłędnie jako fallback.
- FR-002: Użytkownik może przetwarzać wiele plików XML jednocześnie w jednej partii. Priority: must-have
  > Socrates: No counter-argument; it stands as written.
- FR-004: Użytkownik otrzymuje podsumowanie GUI po operacji ze statusem pliku i listą ostrzeżeń. Priority: must-have
  > Socrates: Counter-argument considered: "Okienko może być irytujące dla pracownika przetwarzającego pliki seryjnie". Resolution: Kept for MVP to ensure transparency, possibly making it non-blocking or easy to close with Esc.

### Renderowanie PDF
- FR-003: Użytkownik widzi wizualizację PDF z czytelnym i stałym układem danych (nadawca, adresat, identyfikatory, zdarzenia). Priority: must-have
  > Socrates: No counter-argument; it stands as written.
- FR-005: Użytkownik widzi adnotację o wizualizacji (stopkę) wskazującą, że wiążącym dokumentem pozostaje XML. Priority: nice-to-have
- FR-006: Program przetwarza metadane podpisu XAdES jako sekcję opcjonalną w PDF, bez weryfikacji kryptograficznej. Priority: nice-to-have

## User Stories

### US-01: Przetworzenie pojedynczego lub partii plików XML
- **Given** pracownika kancelarii posiadającego plik(i) EPO w formacie XML
- **When** upuści on pliki na ikonę programu lub użyje opcji "Otwórz za pomocą"
- **Then** w tym samym folderze błyskawicznie pojawiają się czytelne dokumenty PDF
- **And** na ekranie pojawia się małe podsumowanie z ewentualnymi brakami w danych.

## Business Logic

Aplikacja mapuje i waliduje surowe dane XML z e-Doręczeń (niezależnie od ich wariantu XSD) na wspólny, wewnętrzny model kanoniczny Elektronicznego Potwierdzenia Odbioru (EPO), wydobywając wyłącznie ustrukturyzowane informacje prawne (nadawca, adresat, zdarzenia) i oflagowując wszelkie braki. 

Model ten jest następnie podstawą do ustandaryzowanego renderingu PDF, co odcina warstwę wizualną od struktury źródłowej. Aplikacja decyduje, co jest kluczowe w dokumencie dla pracownika administracji i samodzielnie uzupełnia układ wizualny, ukrywając szum z pliku XML.

## Non-Functional Requirements

- Generacja plików PDF dla partii do 50 sztuk kończy się w czasie poniżej 5 sekund (czas odczuwalny przez użytkownika).
- Przetwarzanie i konwersja odbywa się w 100% lokalnie na stacji roboczej, bez absolutnie żadnego wychodzącego ruchu sieciowego.
- Wielkość pojedynczego pliku wykonywalnego nie przekracza 50MB, a aplikacja uruchamia się natychmiast na systemach Windows (10 i 11) bez pre-instalacji innych środowisk uruchomieniowych przez użytkownika.

## Non-Goals

- **Avoid: weryfikacja kryptograficzna podpisów XAdES/CAdES**. Program nie waliduje łańcucha zaufania ani integralności certyfikatu; oryginalny dowód prawny pozostaje w źródłowym pliku XML.
- **Avoid: proces działający w tle (folder-watcher)**. Skupiamy się na procesie uruchamianym manualnie na żądanie użytkownika.
- **Avoid: instalatory klasy korporacyjnej (np. MSI)**. Aplikacja to jeden plik przenośny (portable executable).
- **Avoid: obsługa innych standardów niż e-Doręczenia Poczty Polskiej**. Architekturę zachowujemy otwartą, ale na tym etapie MVP nie budujemy adapterów np. pod ePUAP UPO.
