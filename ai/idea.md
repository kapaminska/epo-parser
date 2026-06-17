# IDEA — Konwerter EPO (XML → PDF) dla Lasów Państwowych

**Status:** szkic koncepcyjny (high-level design)
**Data:** 2026-06-09
**Autor:** (do uzupełnienia)

---

## 1. Cel

Prosty program desktopowy, który zamienia elektroniczne potwierdzenia odbioru (EPO)
otrzymywane z Poczty Polskiej (e-Doręczenia) w formacie XML na czytelny dokument PDF.
Odbiorcą jest Lasy Państwowe; PDF ma służyć jako czytelna, archiwizowalna wizualizacja
doręczenia.

Zakres celowo wąski („prosty programik"): jedno zadanie zrobione dobrze i niezawodnie,
bez rozbudowy ponad realną potrzebę (YAGNI).

---

## 2. Użytkownicy i kontekst

- Maks. **2 stacje robocze z Windows** w Lasach Państwowych.
- Instalacja przechodzi przez **dział IT** odbiorcy (zatwierdzenie + skopiowanie).
- Użytkownicy końcowi są **nietechniczni** — narzędzie musi być oczywiste w obsłudze
  i odporne na błędy.
- Środowisko deweloperskie: **macOS**. Środowisko docelowe: **Windows**.

---

## 3. Zakres funkcjonalny (MVP)

### 3.1 Sposób użycia
- **Przeciągnij i upuść / dwuklik** na pliku XML (lub „Otwórz za pomocą").
- Obsługa **wielu plików naraz** (zaznaczenie i przeciągnięcie grupy).
- Brak procesu w tle, brak folderów-obserwatorów, brak instalatora — uruchamiany na żądanie.

### 3.2 Wejście
- Pliki XML z EPO. Na start: **e-Doręczenia Poczty Polskiej** (dostępny realny przykład).
- Wymóg: architektura **łatwo rozszerzalna o nowe schematy/źródła** w przyszłości.

### 3.3 Wyjście
- **PDF obok źródłowego XML**, z **tą samą nazwą bazową** (`epo_123.xml` → `epo_123.pdf`).
- **Nigdy nie nadpisujemy** istniejącego pliku — przy konflikcie dokładamy sufiks
  (np. `epo_123 (2).pdf`) i odnotowujemy to w podsumowaniu.

### 3.4 Treść PDF
- **Pełny, czytelny szablon** ze wszystkimi istotnymi polami EPO w stałym, ludzkim układzie:
  nadawca, adresat, identyfikatory przesyłki, daty/zdarzenia doręczenia, typ dowodu,
  dane wystawcy/podpisu (jeśli obecne).
- Stały layout — nie surowy zrzut XML i nie dowolna interpretacja.
- **Sekcja „Uwagi / ostrzeżenia"** — widoczne komunikaty o brakujących polach lub
  nierozpoznanym wariancie.
- **Stopka**: adnotacja, że PDF jest wizualizacją, a dokumentem wiążącym pozostaje
  oryginalny (podpisany) plik XML.

### 3.5 Podpis elektroniczny (XAdES)
- Obsługa **opcjonalna i łagodna**: jeśli metadane podpisu/wystawcy są obecne — pokazujemy
  je w PDF; jeśli ich nie ma — pomijamy sekcję bez błędu.
- **Bez kryptograficznej weryfikacji** podpisu w MVP (oryginalny XML pozostaje dowodem).
- Świadomie **nie zakładamy na sztywno**, że EPO z PP nie są podpisywane.

### 3.6 Informacja zwrotna
- **Podwójna**:
  - trwała sekcja „Uwagi" w PDF (ślad dla archiwum/akt),
  - **małe okienko wyników (GUI)** po przetworzeniu: lista `plik → status → ostrzeżenia`
    (np. „epo_456.pdf — 2 ostrzeżenia: brak pola X, nieznany wariant").
- Zasada nadrzędna: **zawsze wygeneruj PDF, gdy to możliwe; nigdy nie wysypuj się po cichu.**

---

## 4. Architektura (high-level)

Podział w duchu DDD / architektury heksagonalnej, w trzech warstwach:

### 4.1 Model kanoniczny EPO
Wewnętrzny, **źródło-niezależny** obiekt domenowy reprezentujący doręczenie ze wszystkimi
istotnymi polami. To „wspólny język" systemu; pozostałe warstwy komunikują się przez niego.

### 4.2 Adaptery źródeł (parsery)
Po jednym na format:
- `PP e-Doręczenia` (MVP),
- w przyszłości np. nowsza wersja XSD PP, `ePUAP UPO`, itd.

Każdy adapter umie wyłącznie: **rozpoznać swój wariant** i **przemapować XML na model
kanoniczny**. Dodanie nowego źródła = dopisanie jednego adaptera, bez ruszania reszty.

### 4.3 Renderer PDF
Jeden, działa **wyłącznie na modelu kanonicznym**. Nie zna formatu źródłowego.
Gwarantuje spójny wygląd PDF niezależnie od źródła.

### 4.4 Dobór adaptera
- **Auto-detekcja** po namespace / elemencie głównym / wersji schematu.
- **Ręczny zapas**: gdy program nie rozpozna wariantu, prosi o wskazanie ręczne
  (zamiast się wysypać). Adapter „nierozpoznany" może wygenerować PDF best-effort
  z wyraźnym ostrzeżeniem.

---

## 5. Technologia i dostarczenie

- **Stos: .NET / C#.**
  - Uzasadnienie: kod powstaje z pomocą LLM (biegłość językowa drugorzędna), a .NET daje
    najczystszą drogę z Maca do niezawodnego pliku Windows.
  - Build: `dotnet publish -r win-x64` → **samodzielny, jednoplikowy `.exe`**
    (self-contained, single-file), **bez zależności** do doinstalowania.
  - Minimalne GUI (np. WinForms) na okienko wyników — mieści się w tym samym `.exe`.
- **Dystrybucja**: IT odbiorcy zatwierdza i kopiuje plik na maks. 2 stacje.
- **Wymóg jakościowy przed wydaniem**: **co najmniej jeden smoke-test na realnym Windowsie**
  (wyłapuje niespodzianki ścieżek/kodowania w cross-buildzie).

---

## 6. Jakość i weryfikacja

- **Testy na próbkach wzorcowych (golden samples):**
  - realne pliki EPO przechowywane jako fixtures,
  - asercje, że adapter wyłuskuje **dokładnie oczekiwane wartości pól** (model kanoniczny),
  - asercje, że PDF zawiera kluczowe wartości,
  - **każdy nowy adapter przychodzi z własną próbką i oczekiwaniami** → ochrona przed regresją.
- **Jednorazowy wizualny przegląd** PDF przy każdej zmianie szablonu.
- Walidacja względem **XSD** — opcjonalnie, jako pomoc przy auto-detekcji, **nie** jako
  główna siatka bezpieczeństwa (sprawdza strukturę, nie poprawność mapowania).

---

## 7. Poza zakresem (na teraz)

- Folder-watcher / usługa w tle / harmonogram.
- Kryptograficzna weryfikacja podpisu (łańcuch certyfikatów, CRL/OCSP, znacznik czasu).
- Konfigurowalny stały folder wyjściowy.
- Masowa konfiguracja / instalator MSI.
- Obsługa źródeł innych niż PP (architektura gotowa, implementacja później).

---

## 8. Ryzyka i sprawy do potwierdzenia

| # | Temat | Do potwierdzenia / ryzyko |
|---|-------|---------------------------|
| 1 | Polskie znaki w PDF | Wybrać i **osadzić font z pełnym zestawem glifów PL** — klasyczna pułapka generatorów PDF (puste „ł/ą/ż"). |
| 2 | Charakter prawny PDF | PDF to wizualizacja, nie oryginał — adnotacja w stopce; dowodem pozostaje podpisany XML. |
| 3 | **PDF/A (archiwizacja)** | Jeśli PDF-y trafiają do archiwum/EZD w LP, może obowiązywać **PDF/A**. Wpływa na wybór biblioteki PDF → **potwierdzić z LP przed startem implementacji renderera.** |
| 4 | Środowisko Windows w LP | Realne ograniczenia stacji (prawa admina, whitelisting) — potwierdzić z IT LP. |
| 5 | Podpisywanie EPO przez PP | Czy/jak EPO z PP są podpisywane i gdzie leży dowód prawny — potwierdzić z dokumentacją PP. |
| 6 | Schematy XSD PP | Czy oficjalne XSD karty EPO są publicznie pobieralne; PP dopuszcza **dwa formaty XSD wymiennie** → adapter musi to znieść. |

---

## 9. Słowniczek

- **EPO** — Elektroniczne Potwierdzenie Odbioru.
- **e-Doręczenia** — publiczna usługa rejestrowanego doręczenia elektronicznego (PURDE/PUH).
- **EZD** — Elektroniczne Zarządzanie Dokumentacją.
- **Model kanoniczny** — wewnętrzna, źródło-niezależna reprezentacja EPO w programie.
- **Adapter** — komponent mapujący konkretny format XML na model kanoniczny.