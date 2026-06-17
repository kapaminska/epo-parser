# EPO Fixture Corpus Implementation Plan

## Overview

Deliver a documented corpus of representative EPO XML samples (`TabletKartaEpo` / `KartaEPO.xsd`) with YAML golden expectations and a pytest verification harness. This gives `S-01` (single-xml-to-pdf-and-txt) a typed canonical-model contract and parametrized golden tests — without implementing the parser or PDF renderer.

## Current State Analysis

Six XML fixtures already exist under `tests/fixtures/` covering five synthetic delivery scenarios plus one real EZD export. All share namespace `http://msepo.gov.pl/epo/XSD/KartaEPO.xsd` and root element `TabletKartaEpo`. No `test_*.py`, no golden expected values, no `domain/` package, and no fixture manifest. Roadmap F-01 is marked **ready** but the change folder is a stub (`change.md` only).

### Key Discoveries:

- Fixtures span `BrakDoreczenia` codes 0–3 and `StatusPrzesylki` 1, 4, 6 — see `tests/fixtures/epo-*.xml`.
- `DaneBiometryczne` appears without `mstns:` prefix in all fixtures — parser must tolerate mixed namespaces.
- Real EZD file keeps production filename: `Wiadomość EZD (Elektroniczne potwierdzenie odbioru - nieodebrana)(3).xml`.
- PRD mentions `nadawca`, but no fixture contains a sender element — **omit from canonical model** (confirmed during planning).
- Second PP XSD variant deferred — document as open risk in manifest; no variant-B fixture in F-01.
- `pyproject.toml` has `lxml` and `pytest` but no `pyyaml` yet.

## Desired End State

After F-01 completes:

1. `domain/model.py` defines minimal dataclass types for the canonical EPO model (no parser logic).
2. `tests/fixtures/README.md` catalogs all six fixtures with scenario descriptions, status-code semantics, and a **Variant B TBD** section.
3. `tests/fixtures/expected/<stem>.yaml` exists for every XML fixture with expected canonical field values and `expected_warnings`.
4. `pytest` passes structural tests (XML well-formed, manifest parity, golden YAML schema validation).
5. `tests/test_pp_epo_parser.py` contains parametrized golden tests marked `@pytest.mark.skip` — ready for S-01 to un-skip.
6. `S-01` is unblocked: implementer has fixtures, typed contract, golden expectations, and test wiring.

### Verification

```bash
pip install -e ".[dev]"
pytest -v
```

All non-skipped tests green; skipped parser golden tests visible in output.

## What We're NOT Doing

- Implementing `parsers/` adapter or XML→canonical mapping (S-01).
- Building `pdf/` renderer or `main.py` orchestration (S-01 / S-02).
- Adding a second XSD variant fixture (deferred until user supplies real sample).
- Adding `nadawca` / sender to canonical model (not present in sample XML).
- Cryptographic XAdES verification or structured XAdES parsing (S-04).
- Vendoring `KartaEPO.xsd` or XSD-based validation as primary safety net.
- Renaming the real EZD export file (keep original filename per planning decision).
- CI GitHub Actions workflow (F-02 / later).

## Implementation Approach

Three incremental phases: (1) typed contract, (2) documented corpus + golden YAML, (3) structural pytest harness with skipped parser tests. Golden YAML is the human-reviewable source of truth; dataclasses mirror its shape so S-01 can compare `parse_pp_epo(path)` output directly. A machine-readable `manifest.yaml` links each XML path to its golden file and scenario metadata — tests derive the fixture list from manifest, not hardcoded filenames.

## Critical Implementation Details

Golden YAML filenames use the XML stem (filename without `.xml`). For the EZD export, the expected file is `tests/fixtures/expected/Wiadomość EZD (Elektroniczne potwierdzenie odbioru - nieodebrana)(3).yaml` — tests must resolve paths via `pathlib`, never shell glob with unquoted spaces.

## Phase 1: Canonical Model Contract

### Overview

Introduce minimal `domain/` types that describe what the PP e-Doręczenia adapter must extract. Types only — no I/O, no XML imports in `domain/`.

### Changes Required:

#### 1. Package scaffold

**File**: `domain/__init__.py`

**Intent**: Expose public canonical model types for tests and future `parsers/` / `pdf/` layers.

**Contract**: Re-export dataclasses from `domain.model` (`EpoDocument`, `Shipment`, `Recipient`, `DeliveryEvent`, `PostalUnit`, `Operator`, `ParseWarning`).

#### 2. Canonical dataclasses

**File**: `domain/model.py`

**Intent**: Define the typed contract S-01 implements against. Fields map to elements/attributes visible in current fixtures; optional sections use `None` or empty defaults.

**Contract**: Dataclasses (frozen or slots per project convention) covering:

- `Recipient` — `name`, `postal_code`, `city`, `street`, `house_number`, `apartment` (all `str | None`)
- `Operator` — `first_name`, `last_name`, `post_office_name`, `post_office_address` from `Wydajacy` attributes
- `PostalUnit` — optional Nadleśnictwo block (`TabletJednostkaMS`): `name`, `department`, address fields
- `DeliveryEvent` — `status_code` (`int`), `non_delivery_code` (`int` from `BrakDoreczenia`), `system_timestamp`, awizo flags/dates, `recipient_signature` (`str | None`)
- `Shipment` — `tracking_number` (`NumerNadania`), `dispatch_date`, `reference` (`Sygnatura`), `kind` (`Rodzaj`), `recipient`, `delivery_event`, `operator`, `postal_unit` (optional), `has_outer_signature` (`bool` — outer `Podpis` blob non-empty)
- `EpoDocument` — `creation_date`, `shipments: list[Shipment]` (MVP fixtures: exactly one), `warnings: list[ParseWarning]`
- `ParseWarning` — `code: str`, `message: str` (machine-readable code + Polish human message)

**No `nadawca` / sender field.** `TabletJednostkaMS` maps to `PostalUnit`, not sender.

#### 3. Dev dependency for YAML

**File**: `pyproject.toml`

**Intent**: Enable golden YAML loading in tests.

**Contract**: Add `pyyaml` to `[dependency-groups] dev`.

### Success Criteria:

#### Automated Verification:

- Package imports cleanly: `python -c "from domain.model import EpoDocument"`
- Type hints present on all public dataclass fields
- `pip install -e ".[dev]"` succeeds with new `pyyaml` dep

#### Manual Verification:

- Dataclass fields align with values written in Phase 2 golden YAML (spot-check one fixture)
- No XML or PDF library imports in `domain/`

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Fixture Manifest & Golden YAML

### Overview

Document the corpus and author per-fixture golden expected canonical values that S-01 will assert against.

### Changes Required:

#### 1. Fixture catalog

**File**: `tests/fixtures/README.md`

**Intent**: Human-readable manifest: what each file exercises, status-code legend, naming conventions, and deferred gaps.

**Contract**: Sections:

- **Corpus index** — table: filename | scenario (PL) | `BrakDoreczenia` | `StatusPrzesylki` | golden YAML path
- **Status codes** — brief legend for `BrakDoreczenia` 0–3 and `StatusPrzesylki` 1/4/6 as used in fixtures
- **Schema variant** — all current files: `TabletKartaEpo` / `KartaEPO.xsd`; **Variant B: TBD** (open roadmap question)
- **Naming** — synthetic `epo-<scenario>.xml`; real EZD keeps original filename
- **Known gaps** — no sender field in XML; outer `Podpis` is PKCS#7 blob not structured XAdES

#### 2. Machine-readable manifest

**File**: `tests/fixtures/manifest.yaml`

**Intent**: Single source of truth for test parametrization — links XML → golden YAML → scenario id.

**Contract**: List of entries:

```yaml
- id: epo-odebrana-osobiscie
  xml: epo-odebrana-osobiscie.xml
  expected: expected/epo-odebrana-osobiscie.yaml
  scenario_pl: "Doręczenie osobiste"
  schema_variant: karta_epo_v1
```

One entry per fixture (6 total). EZD entry uses full original XML filename.

#### 3. Golden expected values

**Files**: `tests/fixtures/expected/<stem>.yaml` (6 files)

**Intent**: Define exact canonical values the PP adapter must extract; include `expected_warnings` for sparse/minimal fixtures.

**Contract**: Each YAML contains:

- `id` — matches manifest `id`
- `schema_variant` — `karta_epo_v1`
- `expected_warnings` — list of `{code, message}` (empty list for complete fixtures; populated for `epo-minimal-puste-pola.xml` and partially for EZD export where fields are empty)
- `document` — nested structure mirroring `EpoDocument` / `Shipment` fields with literal values from the XML (Polish diacritics preserved)

Author golden values by reading each XML fixture directly. Key discriminant scenarios:

| Fixture | Golden focus |
|---------|--------------|
| `epo-odebrana-osobiscie.xml` | `BrakDoreczenia: 0`, recipient signed, biometrics present |
| `epo-awizo-w-placowce.xml` | Awizo flags `1`, both awizo dates populated |
| `epo-jednostka-nadlesnictwo.xml` | `PostalUnit` fully populated (`Nadleśnictwo Sulejówek`) |
| `epo-nieodebrana-analog.xml` | `BrakDoreczenia: 3`, awizo dates, no recipient signature |
| `epo-minimal-puste-pola.xml` | Many `null`/empty fields + warnings for missing address, sygnatura, operator |
| `Wiadomość EZD (...).xml` | Production minified shape; real tracking number; warnings for empty `Miejscowosc`, `Sygnatura`, `Rodzaj` |

### Success Criteria:

#### Automated Verification:

- All 6 golden YAML files exist and parse: `python -c` loop or covered by Phase 3 tests
- `manifest.yaml` entry count equals XML fixture count (6)
- Every `manifest.yaml` `xml` and `expected` path resolves to an existing file

#### Manual Verification:

- README scenario descriptions match actual XML content
- Golden values for `epo-jednostka-nadlesnictwo.yaml` include `Nadleśnictwo Sulejówek` unit fields
- `expected_warnings` on minimal fixture list at least: empty `Miejscowosc`, empty `Sygnatura`, empty `Wydajacy` identity

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Structural Verification Harness

### Overview

Add pytest infrastructure: structural corpus tests (green now) and parametrized parser golden tests (skipped until S-01).

### Changes Required:

#### 1. Shared test fixtures

**File**: `tests/conftest.py`

**Intent**: Central paths and manifest loader for all test modules.

**Contract**:

- `FIXTURES_DIR` — `pathlib.Path` to `tests/fixtures/`
- `load_manifest()` — reads `manifest.yaml`, returns list of entries
- `pytest.fixture` `corpus_entries` — parametrization helper (optional; inline parametrization also acceptable)

#### 2. Structural corpus tests

**File**: `tests/test_fixture_corpus.py`

**Intent**: Automated verification path for F-01 — proves corpus integrity without a parser.

**Contract**: Tests:

- `test_manifest_lists_all_xml_fixtures` — every `*.xml` in `tests/fixtures/` (non-recursive, top-level only) has a manifest entry
- `test_each_fixture_is_well_formed_xml` — `lxml.etree.parse` succeeds for each manifest XML path
- `test_each_fixture_has_parseable_root` — root tag ends with `TabletKartaEpo`, namespace matches `http://msepo.gov.pl/epo/XSD/KartaEPO.xsd`
- `test_each_fixture_has_golden_yaml` — expected path exists
- `test_golden_yaml_matches_document_schema` — load YAML, instantiate or validate against `EpoDocument` field names (helper that checks required keys and types without full parser)
- `test_golden_warnings_are_lists` — `expected_warnings` is a list on every golden file

#### 3. Skipped parser golden tests (S-01 handoff)

**File**: `tests/test_pp_epo_parser.py`

**Intent**: Wire the golden comparison test S-01 will enable by implementing `parsers/pp_edoreczenia.py`.

**Contract**:

- Module-level `@pytest.mark.skip(reason="Parser not implemented — enable in S-01")` on `test_parse_matches_golden` (or per-fixture skip via `pytest.mark.parametrize` over manifest entries)
- Test body calls `parse_pp_epo(xml_path)` (import from `parsers.pp_edoreczenia` — will fail import until S-01; use `pytest.importorskip` or skip at collection time with a stub comment documenting the expected import path)
- Compare returned `EpoDocument` to golden YAML (field-by-field equality helper in test module or `tests/helpers.py`)
- Also compare `warnings` lists (order-insensitive or ordered — document **ordered** to match parser emission order; S-01 implements accordingly)

**Handoff note in file docstring**: S-01 removes skip, implements `parse_pp_epo`, ensures all six parametrized cases pass.

#### 4. Optional comparison helper

**File**: `tests/helpers.py`

**Intent**: Reusable golden comparison for S-01 parser tests and future adapter tests.

**Contract**: `assert_document_matches_golden(actual: EpoDocument, golden: dict) -> None` — raises `AssertionError` with field path on mismatch.

### Success Criteria:

#### Automated Verification:

- `pytest -v` passes all non-skipped tests
- Skipped tests reported: 6 (or 1 parametrized with 6 cases) in `test_pp_epo_parser.py`
- `pytest tests/test_fixture_corpus.py -v` — all structural tests green
- No network calls during test run

#### Manual Verification:

- `pytest -v` output clearly shows skipped parser tests with S-01 reason string
- Running structural tests on macOS with project venv succeeds (develop-on-macOS per tech-stack)

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Testing Strategy

### Unit Tests:

- Manifest parity and file existence (`test_fixture_corpus.py`)
- XML well-formedness and namespace/root element checks
- Golden YAML schema validation against `domain.model` shape
- Warning list structure validation

### Integration Tests:

- None in F-01 (deferred to S-01: XML → canonical model golden match)
- S-01 will un-skip `test_pp_epo_parser.py` as the first integration test

### Manual Testing Steps:

1. Open `tests/fixtures/README.md` — confirm six scenarios documented and Variant B marked TBD.
2. Spot-check `epo-jednostka-nadlesnictwo.yaml` golden vs XML — Nadleśnictwo fields match.
3. Spot-check `epo-minimal-puste-pola.yaml` — warnings list is non-empty and sensible.
4. Run `pytest -v` — confirm structural green, parser skipped.

## Performance Considerations

Negligible — six small XML files, no PDF generation. Full corpus test suite should complete in under 1 second.

## Migration Notes

Not applicable — greenfield foundation slice. Existing six XML fixtures are kept in place; only additions (README, manifest, expected YAML, domain types, tests).

## References

- Roadmap F-01: `context/foundation/roadmap.md` (lines 83–95)
- PRD canonical mapping: `context/foundation/prd.md` (Business Logic)
- Golden-sample pattern: `ai/idea.md` (section 6)
- Testing conventions: `.cursor/rules/testing.mdc`
- Existing fixtures: `tests/fixtures/*.xml`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Canonical Model Contract

#### Automated

- [x] 1.1 Package imports cleanly: `python -c "from domain.model import EpoDocument"`
- [x] 1.2 `pip install -e ".[dev]"` succeeds with `pyyaml` dev dep

#### Manual

- [x] 1.3 Dataclass fields align with golden YAML shape (spot-check after Phase 2, or validate types cover planned golden keys)

### Phase 2: Fixture Manifest & Golden YAML

#### Automated

- [ ] 2.1 All 6 golden YAML files exist and parse without error
- [ ] 2.2 `manifest.yaml` entry count equals XML fixture count; all paths resolve

#### Manual

- [ ] 2.3 README scenarios match XML content; Variant B TBD documented
- [ ] 2.4 Minimal fixture golden includes non-empty `expected_warnings`

### Phase 3: Structural Verification Harness

#### Automated

- [ ] 3.1 `pytest -v` — all non-skipped tests pass
- [ ] 3.2 `pytest tests/test_fixture_corpus.py -v` — structural tests green
- [ ] 3.3 Skipped parser golden tests visible in pytest output (6 cases)

#### Manual

- [ ] 3.4 Structural test run succeeds on macOS dev venv
