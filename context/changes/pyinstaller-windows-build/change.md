---
change_id: pyinstaller-windows-build
title: Pyinstaller windows build
status: implementing
created: 2026-06-17
updated: 2026-06-17
archived_at: null
---

## Notes

### CI artifact

- **Download:** GitHub → Actions → **CI** run on `main` → Artifacts → `epo-parser-windows` → `epo-parser.exe`
- **Windows `.exe` size (CI):** _Pending first green run on `main`._ After push, record the log line `epo-parser.exe size: X MB` here with date and run URL.
- **Hard MB limit:** remains PRD Open Question #1 — user/IT LP decides in S-05 (PRD target ≤ 80 MB).

### S-05 handoff

F-02 delivers CI-built `.exe` artifacts only. S-05 still needs: real Windows LP manual QA, optional GitHub Release, PRD hard size limit decision (and slimming if needed), optional Authenticode signing.

### Dev reference (not CI)

Local macOS one-file smoke build (Phase 1): ~20.3 MB — not representative of Windows `.exe`; use CI log for PRD sizing.
