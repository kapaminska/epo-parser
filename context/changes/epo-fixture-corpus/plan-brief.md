# EPO Fixture Corpus — Plan Brief

> Full plan: `context/changes/epo-fixture-corpus/plan.md`

## What & Why

Build a foundation corpus of representative EPO XML samples with YAML golden expectations and a pytest verification harness so `S-01` (XML → PDF) can implement the parser against a typed contract — not in a vacuum. Roadmap F-01: *reprezentatywne próbki XML EPO i ścieżka weryfikacji ekstrakcji modelu kanonicznego*.

## Starting Point

Six XML fixtures already exist in `tests/fixtures/` (five synthetic scenarios + one real EZD export), all using `TabletKartaEpo` / `KartaEPO.xsd`. No tests, no `domain/` package, no golden values, no manifest. `parsers/`, `pdf/`, and real `main.py` are absent.

## Desired End State

A developer starting `S-01` finds: documented fixtures, `domain/model.py` dataclasses, per-fixture `expected/*.yaml` golden files, green structural pytest, and skipped parametrized parser golden tests ready to un-skip. Running `pytest -v` passes all non-skipped tests.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| -------- | ------ | ---------------- | ------ |
| F-01 scope | Fixtures + golden YAML + test skeleton | Verification path without building parser | Plan |
| Golden format | YAML sidecars in `tests/fixtures/expected/` | Human-readable, diff-friendly field review | Plan |
| Second XSD variant | Defer; document TBD in manifest | No production variant-B sample available yet | Plan |
| EZD real export | Keep original filename | Preserves real-world LP/EZD naming | Plan |
| Canonical model | Minimal dataclasses in `domain/` | Typed contract for S-01 without full domain layer | Plan |
| Nadawca / sender | Omit from model | Not present in sample XML; PRD mention was erroneous for these fixtures | Plan |
| Verification depth | Structural tests green; parser tests skipped | F-01 proves corpus integrity; S-01 enables golden match | Plan |

## Scope

**In scope:**
- `domain/model.py` dataclass types (no parser)
- `tests/fixtures/README.md` + `manifest.yaml`
- Six `expected/*.yaml` golden files
- `tests/test_fixture_corpus.py` (structural)
- `tests/test_pp_epo_parser.py` (skipped golden handoff)
- `pyyaml` dev dependency

**Out of scope:**
- Parser implementation (`parsers/`)
- PDF renderer, CLI orchestration
- Second XSD variant fixture
- `nadawca` field
- CI workflow, XSD vendoring

## Architecture / Approach

```
tests/fixtures/*.xml  ──► manifest.yaml ──► expected/*.yaml
                                │
                                ▼
                         test_fixture_corpus.py  (green: XML + golden integrity)
                                │
                                ▼
                         test_pp_epo_parser.py   (skipped until S-01)
                                │
                                ▼
                         domain/model.py         (typed EpoDocument contract)
```

S-01 implements `parse_pp_epo()` → returns `EpoDocument` → un-skips golden tests.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| ----- | ---------------- | -------- |
| 1. Canonical model contract | `domain/model.py` dataclasses + `pyyaml` dep | Field set too narrow/wide vs real XML |
| 2. Fixture manifest & golden YAML | README, manifest, 6 golden files | Manual YAML authoring errors vs XML |
| 3. Structural verification harness | conftest, structural tests, skipped parser tests | EZD filename path handling with spaces |

**Prerequisites:** Existing six XML fixtures; bootstrapped `pyproject.toml` with `lxml` + `pytest`
**Estimated effort:** ~1–2 sessions across 3 phases

## Open Risks & Assumptions

- Second PP XSD variant may require new fixture + manifest entry when user supplies sample.
- Outer `Podpis` blob treated as presence flag only; structured XAdES deferred to S-04.
- `DaneBiometryczne` unprefixed namespace must be handled by S-01 parser — not tested in F-01.
- EZD export may contain real names; golden YAML should use values from XML as-is (internal test corpus).

## Success Criteria (Summary)

- Six fixtures documented with matching golden YAML and manifest entries.
- `pytest -v` green for structural tests; parser golden tests skipped with clear S-01 message.
- `S-01` implementer can un-skip one test module and implement `parse_pp_epo` against `domain.model`.
