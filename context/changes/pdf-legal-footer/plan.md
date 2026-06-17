# Legal Footer (FR-005) Implementation Plan

## Overview

Roadmap slice **S-03** closes **FR-005**: the user sees a legal visualization disclaimer in the PDF stating that the original signed XML remains the binding document. **S-01 already implemented** the minimal inline disclaimer in `pdf/renderer.py`; this slice formalizes that delivery as the dedicated FR-005 contract — hardened tests, documentation, and a small layout guard — without changing placement (inline after uwagi) or visual styling (9pt DejaVu, left-aligned).

## Current State Analysis

S-01 (`single-xml-to-pdf-and-txt`, status: implemented) shipped:

- `LEGAL_FOOTER` constant with canonical Polish text in `pdf/renderer.py:20-23`
- `_render_legal_footer()` called after `_render_warnings()` in `render_epo_pdf()` (`pdf/renderer.py:47-48`)
- Inline body placement: `ln(6)` + 9pt `multi_cell` (`pdf/renderer.py:152-155`)
- Tests assert both disclaimer sentences in `tests/test_pdf_renderer.py:55-56`

S-01 plan explicitly deferred S-03 scope: *„minimalna stopka wchodzi w S-01"* (`context/changes/single-xml-to-pdf-and-txt/plan.md:42`). S-03 therefore does **not** re-implement the footer — it verifies, documents, and hardens the existing contract.

### Key Discoveries:

- `pdf/renderer.py:48` — footer is end-of-document inline content, not an fpdf2 `footer()` per-page hook
- `tests/test_pdf_renderer.py:55-56` — footer text is tested inside a broad “core sections” test, not as a dedicated FR-005 contract
- No multi-page fixture exists; current fixtures are single-page — acceptable given inline last-page placement decision
- `domain/pipeline.py` and `main.py` need no changes — footer is static renderer concern

## Desired End State

After this plan:

1. Every generated PDF contains the exact `LEGAL_FOOTER` text inline after the **Uwagi / ostrzeżenia** section.
2. `tests/test_pdf_renderer.py` has a dedicated legal-footer test that asserts exact wording and section ordering (uwagi before disclaimer).
3. `LEGAL_FOOTER` and `_render_legal_footer` are documented as the FR-005 delivery point.
4. If the disclaimer would overflow the current page bottom, the renderer starts a new page before rendering it (no mid-line split).

### Verification

```bash
pytest tests/test_pdf_renderer.py -v
pytest -v
```

Manual: open any fixture PDF; confirm disclaimer appears once at the bottom of the document, after uwagi, in readable 9pt Polish text.

## What We're NOT Doing

- Per-page fixed footer via fpdf2 `footer()` hook (user decision: styled inline, last page only)
- Visual restyling: separator lines, centering, italic, or “Informacja prawna” heading (user decision: minimal 9pt left-aligned — same as S-01)
- Wording changes to `LEGAL_FOOTER` text (canonical text from S-01 plan remains)
- PDF/A compliance (`ai/idea.md` §8 — parked pending LP confirmation)
- Changes to `domain/`, `parsers/`, `main.py`, or summary `.txt` format
- Multi-page fixture corpus (not needed for inline last-page footer)

## Implementation Approach

Treat S-03 as a **formalization slice**: audit the existing S-01 implementation against FR-005, add a focused test module contract, document the constant, and add one layout guard. Expect near-zero functional change if audit passes; any gap found is fixed in the same phase.

## Phase 1: Formalize FR-005 inline legal footer

### Overview

Confirm the S-01 footer satisfies FR-005, harden the test contract, document the delivery point, and prevent awkward page-break splits.

### Changes Required:

#### 1. Renderer audit and page-break guard

**File**: `pdf/renderer.py`

**Intent**: Ensure the legal disclaimer always renders completely after uwagi, never split across a page boundary mid-sentence.

**Contract**:

- `_render_legal_footer(pdf)` — before rendering, check remaining vertical space on the current page; if insufficient for the disclaimer block (~15 mm), call `pdf.add_page()` first
- Keep inline placement after `_render_warnings()` in `render_epo_pdf()` — do **not** move to `footer()` hook
- Keep `LEGAL_FOOTER` text unchanged
- Keep 9pt DejaVu, left-aligned, `ln(6)` spacing before text

#### 2. FR-005 documentation

**File**: `pdf/renderer.py`

**Intent**: Make the FR-005 delivery point discoverable for future slices (S-04 XAdES, layout changes).

**Contract**:

- Module-level or constant docstring on `LEGAL_FOOTER` referencing FR-005 and noting inline (not per-page) placement
- Docstring on `_render_legal_footer` describing when it runs in the render sequence

#### 3. Dedicated legal footer tests

**File**: `tests/test_pdf_renderer.py`

**Intent**: Isolate FR-005 as an explicit, independently failing test contract — not buried inside the broad sections test.

**Contract**:

- New test `test_render_epo_pdf_legal_footer_text_and_order`:
  - Assert full `LEGAL_FOOTER` sentences present (import constant or duplicate exact strings)
  - Assert `"Uwagi / ostrzeżenia"` appears before disclaimer text in extracted PDF string
  - Run against at least `epo-odebrana-osobiscie` and `epo-minimal-puste-pola` fixtures (with and without warnings)
- Existing `test_render_epo_pdf_contains_core_sections` may keep footer asserts or delegate to the new test (avoid duplicate assertions — pick one home)

### Success Criteria:

#### Automated Verification:

- `pytest tests/test_pdf_renderer.py -v` — all tests pass, including new legal footer test
- `pytest -v` — full suite green (no regressions)

#### Manual Verification:

- Open `epo-odebrana-osobiscie` output PDF: disclaimer visible once, after uwagi, readable Polish
- Open `epo-minimal-puste-pola` output PDF: disclaimer still present when warnings list is populated

**Implementation Note**: After automated verification passes, pause for manual PDF spot-check before marking the slice complete.

---

## Testing Strategy

### Unit Tests:

- Exact `LEGAL_FOOTER` wording in extracted PDF text
- Section ordering: uwagi heading precedes disclaimer text
- Fixtures with warnings (`epo-minimal-puste-pola`) and without (`epo-odebrana-osobiscie`)

### Integration Tests:

- No new integration tests required — existing pipeline tests confirm PDF generation; FR-005 is renderer-level

### Manual Testing Steps:

1. `python main.py tests/fixtures/epo-odebrana-osobiscie.xml`
2. Open generated PDF in a viewer; scroll to bottom — confirm disclaimer after uwagi
3. Repeat with `epo-minimal-puste-pola.xml` (longer warnings section)

## Performance Considerations

Negligible — one `get_y()` check and optional `add_page()` per PDF. No impact on NFR batch target (50 files / 5s).

## Migration Notes

Not applicable. Existing PDFs generated before this slice already contain the disclaimer; no retroactive regeneration.

## References

- PRD FR-005: `context/foundation/prd.md:65`
- Roadmap S-03: `context/foundation/roadmap.md:138-148`
- S-01 footer contract: `context/changes/single-xml-to-pdf-and-txt/plan.md:222-223`
- Current implementation: `pdf/renderer.py:20-23`, `pdf/renderer.py:47-48`, `pdf/renderer.py:152-155`
- Existing tests: `tests/test_pdf_renderer.py:55-56`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles.

### Phase 1: Formalize FR-005 inline legal footer

#### Automated

- [x] 1.1 `pytest tests/test_pdf_renderer.py -v` — all tests pass, including new legal footer test
- [x] 1.2 `pytest -v` — full suite green (no regressions)

#### Manual

- [x] 1.3 Open fixture PDFs — disclaimer visible once after uwagi, readable Polish
