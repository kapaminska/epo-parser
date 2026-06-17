# Korpus fixture EPO (F-01)

Reprezentatywne próbki XML `TabletKartaEpo` (`KartaEPO.xsd`) z oczekiwanymi wartościami kanonicznymi w `expected/*.yaml`. Służy weryfikacji adaptera PP e-Doręczenia (S-01).

## Indeks korpusu

| Plik XML | Scenariusz | `BrakDoreczenia` | `StatusPrzesylki` | Golden YAML |
| -------- | ---------- | ---------------- | ----------------- | ----------- |
| `epo-odebrana-osobiscie.xml` | Doręczenie osobiste z podpisem odbiorcy | 0 | 1 | `expected/epo-odebrana-osobiscie.yaml` |
| `epo-awizo-w-placowce.xml` | Awizo w placówce — oba znaczniki awizo = 1 | 1 | 4 | `expected/epo-awizo-w-placowce.yaml` |
| `epo-jednostka-nadlesnictwo.xml` | Pełny blok `TabletJednostkaMS` (Nadleśnictwo) | 2 | 6 | `expected/epo-jednostka-nadlesnictwo.yaml` |
| `epo-nieodebrana-analog.xml` | Nieodebrana — doręczenie analogowe, daty awizo | 3 | 6 | `expected/epo-nieodebrana-analog.yaml` |
| `epo-minimal-puste-pola.xml` | Minimalny XML z wieloma pustymi polami | 3 | 6 | `expected/epo-minimal-puste-pola.yaml` |
| `Wiadomość EZD (...).xml` | Produkcyjny eksport EZD (minified) | 3 | 6 | `expected/Wiadomość EZD (...).yaml` |

Źródło prawdy dla testów: `manifest.yaml` (6 wpisów).

## Kody statusu w fixture'ach

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
| 6 | Nieodebrana / w trakcie obsługi (pozostałe) |

## Wariant schematu

Wszystkie bieżące pliki: element główny `TabletKartaEpo`, namespace `http://msepo.gov.pl/epo/XSD/KartaEPO.xsd`.

**Variant B: TBD** — drugi wariant XSD PP e-Doręczeń nie jest jeszcze reprezentowany w korpusie (brak próbki produkcyjnej). Po dostarczeniu próbki: nowy wpis w `manifest.yaml` + golden YAML.

## Konwencje nazewnictwa

- Syntetyczne scenariusze: `epo-<scenariusz>.xml` + `expected/epo-<scenariusz>.yaml`
- Eksport EZD: oryginalna nazwa pliku z systemu (spacje, nawiasy) — bez zmiany

## Znane luki

- **Brak pola nadawca** — żaden fixture nie zawiera elementu nadawcy; model kanoniczny go nie obejmuje.
- **Zewnętrzny `Podpis`** — traktowany jako flaga obecności (`has_outer_signature`); brak parsowania XAdES/PKCS#7 (S-04).
- **`DaneBiometryczne`** — element bez prefiksu `mstns:`; parser S-01 musi tolerować mieszane namespace'y (poza zakresem golden F-01).
