# Korpus fixture EPO (F-01 + S-06)

Reprezentatywne próbki XML z oczekiwanymi wartościami kanonicznymi w `expected/*.yaml`. Służy weryfikacji adapterów PP e-Doręczenia: karta EPO (S-01) i CRD „Potwierdzenie otrzymania” (S-06).

## Indeks korpusu

| Plik XML | Scenariusz | Wariant | Golden YAML |
| -------- | ---------- | ------- | ----------- |
| `epo-odebrana-osobiscie.xml` | Doręczenie osobiste z podpisem odbiorcy | `karta_epo_v1` | `expected/epo-odebrana-osobiscie.yaml` |
| `epo-awizo-w-placowce.xml` | Awizo w placówce — oba znaczniki awizo = 1 | `karta_epo_v1` | `expected/epo-awizo-w-placowce.yaml` |
| `epo-jednostka-nadlesnictwo.xml` | Pełny blok `TabletJednostkaMS` (Nadleśnictwo) | `karta_epo_v1` | `expected/epo-jednostka-nadlesnictwo.yaml` |
| `epo-nieodebrana-analog.xml` | Nieodebrana — doręczenie analogowe, daty awizo | `karta_epo_v1` | `expected/epo-nieodebrana-analog.yaml` |
| `epo-minimal-puste-pola.xml` | Minimalny XML z wieloma pustymi polami | `karta_epo_v1` | `expected/epo-minimal-puste-pola.yaml` |
| `Wiadomość EZD (...).xml` | Produkcyjny eksport EZD (minified) | `karta_epo_v1` | `expected/Wiadomość EZD (...).yaml` |
| `ZW.224.1.856.2025 (Potwierdzenie otrzymania).xml` | CRD — adresat osoba fizyczna, 2 załączniki | `crd_potwierdzenie_otrzymania_v1` | `expected/crd-zw-856-2025.yaml` |
| `Znak sprawy_ ZW.224.1.840.2025 (...).xml` | CRD — adresat osoba prawna, 3 załączniki | `crd_potwierdzenie_otrzymania_v1` | `expected/crd-zw-840-2025.yaml` |
| `Znak sprawy_ ZW.224.1.932.2025 (...).xml` | CRD — brak sygnatury `ZW.*` w załącznikach | `crd_potwierdzenie_otrzymania_v1` | `expected/crd-zw-932-2025.yaml` |

Źródło prawdy dla testów: `manifest.yaml` (9 wpisów).

## Kody statusu w fixture'ach karta EPO

### `BrakDoreczenia`

| Kod | Znaczenie w korpusie |
| --- | -------------------- |
| 0 | Doręczenie osobiste (`epo-odebrana-osobiscie`) |
| 1 | Awizo w placówce (`epo-awizo-w-placowce`) |
| 2 | Awizo / jednostka MS (`epo-jednostka-nadlesnictwo`) |
| 3 | Nieodebrana / analog (`epo-nieodebrana-analog`, `epo-minimal-puste-pola`, EZD) |

### `StatusPrzesylki`

| Kod | Występuje w |
| --- | ----------- |
| 1 | Doręczenie zakończone (`epo-odebrana-osobiscie`) |
| 4 | Awizo (`epo-awizo-w-placowce`) |
| 6 | Nieodebrana / w trakcie obsługi (pozostałe karta EPO) |

## Warianty schematu

### `karta_epo_v1`

Element główny `TabletKartaEpo`, namespace `http://msepo.gov.pl/epo/XSD/KartaEPO.xsd`.

### `crd_potwierdzenie_otrzymania_v1`

Element główny `Dokument`, namespace `http://crd.gov.pl/wzor/2021/09/01/10856/` (wzór 10856/2021 — „Potwierdzenie otrzymania”). Osoby fizyczne używają namespace `http://crd.gov.pl/xml/schematy/osoba/2009/11/16/`.

## Konwencje nazewnictwa

- Syntetyczne scenariusze karta EPO: `epo-<scenariusz>.xml` + `expected/epo-<scenariusz>.yaml`
- Eksport EZD: oryginalna nazwa pliku z systemu (spacje, nawiasy) — bez zmiany
- CRD produkcyjne: `expected/crd-zw-<sygnatura>.yaml` (skrót od numeru sprawy w nazwie pliku)

## Znane luki

- **Nadawca w karcie EPO** — żaden fixture `karta_epo_v1` nie zawiera nadawcy; pole `sender` w modelu kanonicznym jest `null`.
- **Zewnętrzny podpis** — traktowany jako flaga obecności (`has_outer_signature`); brak parsowania XAdES/PKCS#7 (S-04).
- **`DaneBiometryczne`** — element bez prefiksu `mstns:`; parser S-01 musi tolerować mieszane namespace'y (poza zakresem golden F-01).
