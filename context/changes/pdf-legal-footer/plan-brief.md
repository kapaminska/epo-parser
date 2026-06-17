# Legal Footer (FR-005) — Plan Brief

> Full plan: `context/changes/pdf-legal-footer/plan.md`

## What & Why

FR-005 requires users to see a legal disclaimer in the PDF stating it is only a visualization and the original signed XML remains binding. S-01 already shipped the minimal inline disclaimer; S-03 formally closes this nice-to-have requirement with hardened tests and documentation rather than re-building the footer.

## Starting Point

`pdf/renderer.py` renders `LEGAL_FOOTER` inline after **Uwagi / ostrzeżenia** (9pt DejaVu, left-aligned). `tests/test_pdf_renderer.py` asserts disclaimer text inside a broad sections test. S-01 explicitly pulled minimal footer into core delivery and deferred S-03.

## Desired End State

Every PDF contains the canonical disclaimer text after uwagi. A dedicated FR-005 test asserts exact wording and section order. The renderer avoids splitting the disclaimer mid-line across a page break. No visual or placement changes from S-01.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| --- | --- | --- | --- |
| Placement | Inline after uwagi (last page) | Smallest diff; S-01 already works this way | Plan |
| Per-page footer | No — skip `footer()` hook | User accepted last-page-only tradeoff for multi-page prints | Plan |
| Visual styling | Minimal 9pt left-aligned | Matches existing S-01 renderer; no formal separator | Plan |
| Wording | Keep S-01 canonical text | Already approved in S-01 plan and tested | Plan |
| Scope of work | Formalize + harden, not rebuild | S-01 delivered the footer; S-03 closes FR-005 contract | Plan |

## Scope

**In scope:**

- Page-break guard before disclaimer rendering
- FR-005 docstrings on `LEGAL_FOOTER` / `_render_legal_footer`
- Dedicated legal footer test (text + ordering)
- Manual PDF spot-check

**Out of scope:**

- Per-page fixed footer, visual restyling, wording changes
- PDF/A, domain/parser/main changes, multi-page fixtures

## Architecture / Approach

Single-file touch: `pdf/renderer.py` (audit + optional page-break guard + docs). Tests in `tests/test_pdf_renderer.py`. Pipeline and CLI unchanged — footer is static renderer output at the end of the section sequence.

```
render_epo_pdf → … → _render_warnings → _render_legal_footer → output
```

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Formalize FR-005 inline legal footer | Hardened test contract, docs, page-break guard | Near-zero delta — slice may feel trivial if audit passes cleanly |

**Prerequisites:** S-01 implemented (met)
**Estimated effort:** ~1 session, single phase

## Open Risks & Assumptions

- Assumption: inline last-page disclaimer is acceptable to LP users (accepted tradeoff vs per-page footer)
- Risk: slice delivers little visible change — value is FR-005 traceability and test isolation
- Assumption: current single-page fixtures suffice; no multi-page EPO samples in corpus yet

## Success Criteria (Summary)

- Dedicated test fails if disclaimer text or uwagi ordering regresses
- Full `pytest` suite green
- Manual PDF check confirms disclaimer readable at document bottom
