---
change_id: pyinstaller-windows-build
title: Pyinstaller windows build
status: archived
created: 2026-06-17
updated: 2026-06-17
archived_at: 2026-06-17T20:09:32Z
---

## Notes

### CI artifact

- **Download:** GitHub → Actions → **CI** run on `main` → Artifacts → `epo-parser-windows` → `epo-parser.exe`
- **Windows `.exe` size (CI):** **23.1 MB** — first green run 2026-06-17, [Actions run #5](https://github.com/kapaminska/epo-parser/actions/runs/27715469979) (`a6897fc`)
- **Hard MB limit:** remains PRD Open Question #1 — user/IT LP decides in S-05 (PRD target ≤ 80 MB). First CI build is **within target**.

### S-05 handoff

F-02 delivers CI-built `.exe` artifacts only. S-05 still needs: real Windows LP manual QA, optional GitHub Release, PRD hard size limit sign-off (if IT LP accepts 23.1 MB), optional Authenticode signing.

### Dev reference (not CI)

Local macOS one-file smoke build (Phase 1): ~20.3 MB — not used for PRD sizing; Windows CI artifact is authoritative.
