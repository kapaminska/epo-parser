## EPO Parser 0.2.0

Konwerter plików XML z e-Doręczeń Poczty Polskiej na PDF (karta EPO + Potwierdzenie otrzymania CRD).

### Jak używać

1. **Pobierz** plik `epo-parser.exe` z sekcji **Assets** poniżej.
2. **Skopiuj** go do folderu ze sprawą — tam, gdzie leżą pliki `.xml`.
3. **Kliknij dwukrotnie** na `epo-parser.exe`.

Pojawi się **czarne okno** (konsola). **Nie zamykaj go ręcznie** — program sam zakończy pracę i okno zniknie, gdy skończy przetwarzać pliki.

**Pliki wynikowe** (PDF-y oraz `epo-konwersja.txt` z podsumowaniem) zapiszą się **w tym samym folderze** co pliki XML.

### Ważne

- Nie trzeba instalować Pythona — program działa offline.
- Istniejące PDF-y **nie są nadpisywane** — przy tej samej nazwie powstanie np. ` (2).pdf`.
- Szczegóły i ewentualne błędy: plik **`epo-konwersja.txt`** w folderze sprawy.

### Wymagania

Windows 10 lub 11 (64-bit).
