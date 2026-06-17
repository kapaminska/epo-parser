---
project: "EPO Parser"
version: 2
status: draft
created: 2026-06-17
updated: 2026-06-17
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
---

## Vision & Problem Statement

Pracownicy administracyjni / kancelarii w Lasach Państwowych otrzymują Elektroniczne Potwierdzenia Odbioru (EPO) z e-Doręczeń Poczty Polskiej w surowym formacie XML, co powoduje, że dane są "uwięzione" – brakuje możliwości łatwego odczytania i zarchiwizowania wizualizacji dokumentu. Kosztuje ich to utrudnione procesowanie spraw i brak czytelnego archiwum.

Zauważyliśmy, że Poczta Polska nie dostarcza przyjaznego, czytelnego wariantu EPO (np. PDF) w standardzie, co tworzy lukę, którą to proste narzędzie offline idealnie wypełnia.

## User & Persona

Pracownik administracji / kancelarii w Lasach Państwowych. Osoba nietechniczna, która na co dzień obsługuje przesyłki i potrzebuje niezawodnie, szybko zamienić plik XML na czytelny PDF do wpięcia do akt.

## Success Criteria

### Primary
1. Użytkownik uruchamia `epo-parser.exe` dwuklikiem w folderze z plikami XML (lub przez „Otwórz za pomocą” na wybranych plikach).
2. Aplikacja generuje czytelne pliki PDF obok źródeł z tą samą nazwą bazową.
3. Aplikacja zapisuje plik tekstowy podsumowania (`epo-konwersja.txt`) w folderze roboczym ze statusem każdego pliku i listą ostrzeżeń.

### Secondary
- Czytelne sekcje z uwagami / brakami w samym dokumencie PDF, w razie problemów z parsowaniem pliku XML.
- Nigdy nie nadpisujemy istniejącego pliku wyjściowego — przy konflikcie dokładamy sufiks, np. `epo_123 (2).pdf` lub `epo-konwersja (2).txt`.

### Guardrails
- Aplikacja zawsze wygeneruje PDF, jeśli to tylko możliwe; nigdy nie wysypuje się po cichu (no silent crashes). Przy braku plików XML w folderze użytkownik dostaje czytelny komunikat w pliku podsumowania (nie pusty wynik bez śladu).
- Pozostaje pojedynczym plikiem wykonywalnym (`.exe`) i nie wymaga instalacji Pythona, konfiguracji folderów w tle ani uprawnień admina.

## User Stories

### US-01: Przetworzenie pojedynczego lub partii plików XML
- **Given** pracownika kancelarii posiadającego plik(i) EPO w formacie XML w jednym folderze
- **When** uruchomi on `epo-parser.exe` w tym folderze (lub użyje „Otwórz za pomocą” na pliku XML)
- **Then** w tym samym folderze błyskawicznie pojawiają się czytelne dokumenty PDF
- **And** w folderze pojawia się plik `epo-konwersja.txt` (lub `epo-konwersja (2).txt` itd.) z podsumowaniem i ewentualnymi brakami w danych.

## Functional Requirements

### Przetwarzanie
- FR-001: Użytkownik uruchamia program dwuklikiem w folderze z plikami XML — program przetwarza wszystkie `.xml` w bieżącym katalogu. Fallback: „Otwórz za pomocą” / argumenty CLI ze ścieżkami do plików. Priority: must-have
  > Socrates: Counter-argument considered: "Użytkownik może uruchomić .exe z niewłaściwego folderu". Resolution: Kept primary flow (exe w katalogu); przy braku XML — jawne podsumowanie w `.txt`; fallback CLI dla pojedynczych pl spoza folderu.
- FR-002: Użytkownik może przetwarzać wiele plików XML jednocześnie w jednej partii (skan katalogu lub wiele ścieżek CLI). Priority: must-have
  > Socrates: No counter-argument; it stands as written.
- FR-004: Użytkownik otrzymuje plik tekstowy podsumowania po operacji (`epo-konwersja.txt`) ze statusem każdego pliku i listą ostrzeżeń; kolejne uruchomienia używają sufiksów `(2)`, `(3)` itd., bez nadpisywania poprzednich podsumowań. Priority: must-have
  > Socrates: Counter-argument considered: "Plik txt jest mniej widoczny niż okienko GUI". Resolution: Accepted — txt daje trwały ślad w folderze sprawy, spójny z archiwizacją akt; uwagi nadal trafiają też do PDF.

### Renderowanie PDF
- FR-003: Użytkownik widzi wizualizację PDF z czytelnym i stałym układem danych (nadawca, adresat, identyfikatory, zdarzenia). Priority: must-have
  > Socrates: No counter-argument; it stands as written.
- FR-005: Użytkownik widzi adnotację o wizualizacji (stopkę) wskazującą, że wiążącym dokumentem pozostaje XML. Priority: nice-to-have
- FR-006: Program przetwarza metadane podpisu XAdES jako sekcję opcjonalną w PDF, bez weryfikacji kryptograficznej. Priority: nice-to-have

## Non-Functional Requirements

- Generacja plików PDF dla partii do 50 sztuk kończy się w czasie poniżej 5 sekund (czas odczuwalny przez użytkownika).
- Przetwarzanie i konwersja odbywa się w 100% lokalnie na stacji roboczej, bez absolutnie żadnego wychodzącego ruchu sieciowego.
- Dostawa jako pojedynczy przenośny plik `.exe` (PyInstaller one-file) na Windows 10 i 11, bez pre-instalacji Pythona przez użytkownika. Docelowy rozmiar ≤ 80 MB; twardy limit ustalany po pierwszym buildzie CI. Czas uruchomienia akceptowalny dla użytkownika biurowego (dopuszczalne krótkie rozpakowanie one-file).

## Business Logic

Aplikacja mapuje i waliduje surowe dane XML z e-Doręczeń (niezależnie od ich wariantu XSD) na wspólny, wewnętrzny model kanoniczny Elektronicznego Potwierdzenia Odbioru (EPO), wydobywając wyłącznie ustrukturyzowane informacje prawne (nadawca, adresat, zdarzenia) i oflagowując wszelkie braki.

Model ten jest następnie podstawą do ustandaryzowanego renderingu PDF, co odcina warstwę wizualną od struktury źródłowej. Aplikacja decyduje, co jest kluczowe w dokumencie dla pracownika administracji i samodzielnie uzupełnia układ wizualny, ukrywając szum z pliku XML.

Przy każdej operacji program zapisuje plik podsumowania tekstowego w bieżącym katalogu roboczym, stosując tę samą regułę sufiksów co dla PDF.

## Access Control

Single user; no auth; data lives on-device only. (Narzędzie desktopowe uruchamiane na żądanie bez rejestracji i logowania).

## Non-Goals

- **Avoid: weryfikacja kryptograficzna podpisów XAdES/CAdES**. Program nie waliduje łańcucha zaufania ani integralności certyfikatu; oryginalny dowód prawny pozostaje w źródłowym pliku XML.
- **Avoid: proces działający w tle (folder-watcher)**. Skupiamy się na procesie uruchamianym manualnie na żądanie użytkownika.
- **Avoid: instalatory klasy korporacyjnej (np. MSI)**. Aplikacja to jeden plik przenośny (portable executable).
- **Avoid: graficzny interfejs użytkownika (GUI / okienka / frontend webowy)**. Informacja zwrotna wyłącznie przez PDF (sekcja uwag) i plik `.txt`.
- **Avoid: obsługa innych standardów niż e-Doręczenia Poczty Polskiej**. Architekturę zachowujemy otwartą, ale na tym etapie MVP nie budujemy adapterów np. pod ePUAP UPO.

## Open Questions

1. **Jaki twardy limit rozmiaru `.exe` ustalić po pierwszym buildzie PyInstaller?** — Owner: user / IT LP. Block: no (do czasu `windows-portable-delivery`).
