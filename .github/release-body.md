## EPO Parser — konwerter XML → PDF dla Lasów Państwowych

Narzędzie offline do przetwarzania plików XML z e-Doręczeń Poczty Polskiej na czytelne PDF-y w folderze sprawy.

### Co nowego w tej wersji

- Karta EPO (`TabletKartaEpo`) — doręczenia pocztowe, awizo, jednostki MS
- **Potwierdzenie otrzymania CRD** (wzór 10856/2021) — nadawca, adresat AE, załączniki
- Batch: wszystkie pliki `.xml` w bieżącym folderze
- Podsumowanie w pliku `epo-konwersja.txt`

### Instalacja (Windows 10 / 11)

1. Pobierz **`epo-parser.exe`** z sekcji Assets poniżej.
2. Skopiuj plik do folderu ze sprawą (tam, gdzie leżą pliki `.xml`).
3. Uruchom **`epo-parser.exe`** (dwuklik).

Program utworzy pliki PDF obok XML oraz plik **`epo-konwersja.txt`** z podsumowaniem.

**Nie wymaga Pythona ani instalacji** — działa w całości offline.

### Wskazówki

- Istniejące PDF-y i pliki podsumowania **nie są nadpisywane** — przy kolizji nazw dodawany jest sufiks, np. ` (2).pdf`.
- Obsługiwane formaty: karta EPO oraz CRD „Potwierdzenie otrzymania” z e-Doręczeń PP.
- W razie błędu szczegóły są w `epo-konwersja.txt`.

### Wymagania

- Windows 10 lub 11 (64-bit)
- Pliki XML wyeksportowane z e-Doręczeń Poczty Polskiej

---

Szczegóły techniczne i rozwój: [repozytorium](https://github.com/kapaminska/epo-parser).
