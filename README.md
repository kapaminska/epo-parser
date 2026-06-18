# EPO Parser

Offline desktop tool for **Lasów Państwowych**: converts Polish Post e-Doręczenia XML files to readable PDFs in the working directory, with a text summary (`epo-konwersja.txt`).

Supported formats: **karta EPO** (`TabletKartaEpo`) and **CRD Potwierdzenie otrzymania** (wzór 10856/2021).

## Windows — pobierz i użyj

**[Pobierz najnowszą wersję (GitHub Releases)](https://github.com/kapaminska/epo-parser/releases/latest)**

1. Pobierz `epo-parser.exe` z sekcji **Assets** na stronie release.
2. Skopiuj plik do folderu ze sprawą (pliki `.xml`).
3. Uruchom `epo-parser.exe` (dwuklik).

Powstaną pliki PDF oraz `epo-konwersja.txt` z podsumowaniem konwersji. **Python nie jest potrzebny** — program działa offline.

Przy kolizji nazw plików wyjściowych dodawany jest sufiks, np. ` (2).pdf` (istniejące pliki nie są nadpisywane).

## Developers

```bash
pip install -e ".[dev]"
pytest
python main.py                    # batch w bieżącym katalogu
python main.py plik.xml           # pojedynczy plik
```

Build Windows `.exe` (maintainers):

- Każdy push na `main` → workflow **Windows Build** → artefakt `epo-parser-windows` w Actions.
- Tag `v*` (np. `v0.2.0`) → ten sam build + publikacja na **[GitHub Releases](https://github.com/kapaminska/epo-parser/releases)**.

Lokalnie (Windows): `pyinstaller epo-parser.spec --noconfirm` → `dist/epo-parser.exe`.

## Dokumentacja produktu

- `context/foundation/prd.md` — wymagania
- `context/foundation/roadmap.md` — roadmapa
- `context/foundation/tech-stack.md` — stack
