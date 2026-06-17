# PyInstaller Windows Build — Plan Brief

> Full plan: `context/changes/pyinstaller-windows-build/plan.md`

## What & Why

Roadmap **F-02** delivers a PyInstaller + GitHub Actions foundation so the project produces a one-file `epo-parser.exe` on `windows-latest` without manual Windows build setup. This unlocks **S-05** (portable delivery to LP workstations) and surfaces real `.exe` size for PRD Open Question #1.

## Starting Point

The CLI pipeline works (`main.py`, `domain/`, `parsers/`, `pdf/`, green `pytest`). Packaging is specified in `tech-stack.md` and bootstrap hints but absent in code: no `.github/workflows/`, no `.spec`, no `pyinstaller` dep. Font `pdf/assets/DejaVuSans.ttf` must be bundled for PDF rendering on Windows.

## Desired End State

Every push to `main` runs `pytest` then PyInstaller on Windows, uploads `epo-parser.exe` as a GHA artifact, smoke-tests `--help`, and logs file size in MB. Maintainers download the `.exe` from Actions; S-05 picks up LP manual QA and optional GitHub Release.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| -------- | ------ | ---------------- | ------ |
| CI trigger | Push to `main` | Matches tech-stack `build-on-merge` hint | Plan |
| Workflow shape | Single job: pytest + PyInstaller | One green gate before artifact | Plan |
| PyInstaller config | Committed `epo-parser.spec` | Reproducible datas/hiddenimports; workflow stays thin | Plan |
| Artifact delivery | GHA `upload-artifact` only | Foundation skeleton; releases in S-05 | Plan |
| Post-build smoke | `--help` only | Fast signal without fixture I/O in CI | Plan |
| Python version | 3.14 | Matches `pyproject.toml` `requires-python` | Plan |

## Scope

**In scope:**
- `pyinstaller` dev dependency
- `epo-parser.spec` (onefile, console, font datas, lxml/fontTools collection)
- `.github/workflows/ci.yml` on `windows-latest`
- CI size logging + F-02/S-05 handoff notes

**Out of scope:**
- GitHub Releases, signing, PR builds
- Windows LP double-click / Open-with QA (S-05)
- End-to-end `.exe` fixture conversion in CI
- PRD hard MB limit decision (log only)

## Architecture / Approach

```
push main → GHA windows-latest (Python 3.14)
              ├── pip install -e ".[dev]"
              ├── pytest -v
              ├── pyinstaller epo-parser.spec
              ├── epo-parser.exe --help  (smoke)
              ├── log size (MB)
              └── upload-artifact → epo-parser.exe
```

Spec owns bundling rules (`main.py`, packages, `DejaVuSans.ttf`, lxml binaries); workflow orchestrates only.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| ----- | ---------------- | -------- |
| 1. Spec & dev deps | `epo-parser.spec` + pyinstaller in dev group | Missing lxml `.pyd` or font `datas` |
| 2. GHA workflow | Combined test + build + artifact + smoke | Python 3.14 availability on runner |
| 3. Handoff | Size in change notes; S-05 unblocked | `.exe` exceeds 80 MB target |

**Prerequisites:** Green `pytest` on current `main`; repo on GitHub with Actions enabled
**Estimated effort:** ~1 session across 3 phases

## Open Risks & Assumptions

- Python 3.14 + PyInstaller combo may need version pin or pre-release on GHA — workflow comment documents fallback.
- Font path via `__file__` may need `_MEIPASS` helper in S-05 if PDF fails despite passing `--help`.
- First build size unknown; slimming deferred to S-05 if over PRD target.

## Success Criteria (Summary)

- Push to `main` → green CI with downloadable `epo-parser.exe` artifact.
- CI log reports `.exe` size in MB for PRD decision.
- S-05 can start Windows LP verification without inventing build plumbing.
