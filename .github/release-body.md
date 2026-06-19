## EPO Parser

Konwerter plików XML z e-Doręczeń Poczty Polskiej na PDF (karta EPO + Potwierdzenie otrzymania CRD).

### Jak używać

1. **Pobierz** plik **`epo-parser.zip`** z sekcji **Assets** poniżej (nie `.exe` — sieci firmowe często blokują sam plik wykonywalny).
2. **Rozpakuj** ZIP (PPM → *Wyodrębnij wszystko*).
3. **Skopiuj** `epo-parser.exe` do folderu ze sprawą — tam, gdzie leżą pliki `.xml`.
4. **Kliknij dwukrotnie** na `epo-parser.exe`.

Pojawi się **czarne okno** (konsola). **Nie zamykaj go ręcznie** — program sam zakończy pracę i okno zniknie, gdy skończy przetwarzać pliki.

**Pliki wynikowe** (PDF-y oraz `epo-konwersja.txt`) zapiszą się **w tym samym folderze** co pliki XML.

W archiwum jest też plik **`INSTRUKCJA.txt`** z tą samą instrukcją.

### Ważne

- Nie trzeba instalować Pythona — program działa offline.
- Istniejące PDF-y **nie są nadpisywane** — przy tej samej nazwie powstanie np. ` (2).pdf`.
- Szczegóły i ewentualne błędy: plik **`epo-konwersja.txt`** w folderze sprawy.

### Wymagania

Windows 10 lub 11 (64-bit).
