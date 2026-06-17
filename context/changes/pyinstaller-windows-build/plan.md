# PyInstaller Windows Build Implementation Plan

## Overview

Deliver roadmap **F-02**: a committed PyInstaller spec and a GitHub Actions workflow on `windows-latest` that runs the existing test suite, builds a one-file `epo-parser.exe`, smoke-tests `--help`, logs artifact size, and uploads the `.exe` as a downloadable GHA artifact. This unlocks **S-05** (Windows portable delivery) without requiring manual PyInstaller setup from scratch.

## Current State Analysis

The application is a working Python CLI (`main.py` → `domain/` → `parsers/` + `pdf/`) with `pytest` coverage and batch conversion (S-02). Packaging is documented in `tech-stack.md` and bootstrap hints but **not implemented**:

- No `.github/workflows/`
- No `*.spec` file
- No `pyinstaller` dependency in `pyproject.toml`
- `.gitignore` already excludes `dist/`, `build/`, `*.spec.bak`

Prior slices explicitly defer CI/PyInstaller to F-02; Windows LP double-click / Open-with manual QA stays in S-05.

### Key Discoveries:

- Entry point: `epo-parser = "main:main"` in `pyproject.toml` (L16–17); `main.py` lives at repo root alongside packages `domain/`, `parsers/`, `pdf/` (Hatch wheel config L35–40).
- Bundled asset required: `pdf/assets/DejaVuSans.ttf` resolved via `Path(__file__).parent / "assets"` in `pdf/renderer.py` (L19) — must appear in PyInstaller `datas` at `pdf/assets/DejaVuSans.ttf`.
- Native / transitive deps: `lxml.etree` (`.pyd` binaries on Windows); `fpdf2` pulls `fontTools` for custom TTF via `add_font`.
- Bootstrap hints (`context/changes/bootstrap-verification/verification.md`): `github-actions`, `build-on-merge`, `github-releases` — F-02 implements build-on-merge with **GHA artifacts only** (releases deferred to S-05).
- PRD NFR: one-file portable `.exe`, Windows 10/11, target ≤ 80 MB; hard limit decided after first CI build (Open Question #1).

## Desired End State

After F-02 completes:

1. `pyinstaller` is listed in dev dependencies; `epo-parser.spec` is committed with one-file console configuration, font `datas`, and `lxml` / `fontTools` collection.
2. `.github/workflows/ci.yml` runs on **push to `main`** on `windows-latest` with Python **3.14**: `pytest` → PyInstaller build → `epo-parser.exe --help` smoke → log file size → `upload-artifact`.
3. A maintainer can download `epo-parser.exe` from the GitHub Actions run summary without local Windows tooling.
4. CI log output includes `.exe` size in MB for PRD Open Question #1 (hard limit decision in S-05).
5. **S-05** is unblocked for real-machine Windows verification and optional GitHub Release wiring.

### Verification

```bash
# Local (macOS): pytest still passes; PyInstaller build is CI-only for F-02
pip install -e ".[dev]"
pytest -v

# CI (automatic on push to main): green workflow with artifact + size line in logs
```

## What We're NOT Doing

- GitHub Releases / semver tagging / draft releases (S-05 or later).
- Authenticode signing or IT LP whitelisting steps.
- Windows LP manual QA (double-click batch, Open-with) — S-05.
- macOS or Linux PyInstaller builds.
- CI on pull requests (push-to-`main` only per planning decision).
- End-to-end fixture conversion smoke in CI (`--help` only for F-02).
- `_MEIPASS` runtime helper changes in `pdf/renderer.py` unless first CI build proves font path fails (defer fix to S-05 if needed).
- Perf gate (50 XML / 5 s) in CI.
- Updating PRD hard MB limit — log size only; user/IT LP decides in S-05.

## Implementation Approach

Three incremental phases: (1) reproducible PyInstaller spec in-repo, (2) combined GHA workflow exercising tests then build, (3) size visibility and handoff notes for S-05. Keep the spec as the single source of PyInstaller options; the workflow invokes `pyinstaller epo-parser.spec` without duplicating flags. Use `pip install -e ".[dev]"` in CI (matches AGENTS.md; no uv requirement on GHA).

## Critical Implementation Details

**Font path in one-file mode:** PyInstaller must place `DejaVuSans.ttf` at `pdf/assets/DejaVuSans.ttf` relative to the extracted module tree so `FONT_PATH = Path(__file__).resolve().parent / "assets" / "DejaVuSans.ttf"` continues to work. If CI `--help` passes but a manual PDF run fails with missing font, S-05 adds a frozen-runtime path helper — do not preemptively refactor renderer in F-02.

**Python 3.14 on GHA:** Use `actions/setup-python@v5` with `python-version: "3.14"`. If the runner image lacks 3.14 at implementation time, pin the latest available 3.14.x pre-release and document the pin in the workflow comment — do not downgrade to 3.12/3.13 without a new planning decision.

## Phase 1: PyInstaller Spec & Dev Dependencies

### Overview

Add PyInstaller as a dev dependency and commit a spec file that bundles the CLI entry, all packages, the DejaVu font, and native/transitive imports.

### Changes Required:

#### 1. Dev dependency

**File**: `pyproject.toml`

**Intent**: Make PyInstaller available locally and in CI via the existing dev install path.

**Contract**: Add `pyinstaller` (pin a recent stable version, e.g. `>=6.0.0`) to both `[project.optional-dependencies] dev` and `[dependency-groups] dev`.

#### 2. PyInstaller spec

**File**: `epo-parser.spec` (repo root)

**Intent**: Single committed source for one-file Windows console build of `epo-parser.exe`.

**Contract**:

- **Mode:** `onefile`, console (not `windowed`) — CLI tool with stdout/stderr for errors and no GUI.
- **Entry:** `main.py` (script analysis root matching current layout).
- **Name:** `epo-parser` → output `dist/epo-parser.exe`.
- **Packages:** collect `domain`, `parsers`, `pdf` (via `pathex` including repo root or explicit module collection).
- **Datas:** `('pdf/assets/DejaVuSans.ttf', 'pdf/assets')` (Windows path separator handled by spec/OS).
- **Hidden imports / collection:** include at minimum `lxml.etree`, `lxml._elementpath`, `fpdf`, `fontTools`, `fontTools.ttLib`; prefer `collect_all('lxml')` or equivalent hook-friendly collection for native `.pyd` files.
- **UPX:** disabled (`upx=False`) — predictable size reporting for PRD open question.
- Spec is checked in; `dist/` and `build/` remain gitignored.

### Success Criteria:

#### Automated Verification:

- `pip install -e ".[dev]"` succeeds with `pyinstaller` importable
- `pytest -v` still passes (no runtime behavior change)

#### Manual Verification:

- Spec file reviewed: `datas` includes font; entry is `main.py`; mode is onefile console

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: GitHub Actions CI Workflow

### Overview

Add a combined workflow on `windows-latest` that validates tests, builds the `.exe`, smoke-tests `--help`, logs size, and uploads the artifact.

### Changes Required:

#### 1. CI workflow

**File**: `.github/workflows/ci.yml`

**Intent**: Automate test + PyInstaller build on every push to `main` per tech-stack `build-on-merge` hint.

**Contract**:

- **Trigger:** `push` to branch `main` only (no `pull_request` trigger in F-02).
- **Runner:** `windows-latest`.
- **Python:** `3.14` via `actions/setup-python@v5`.
- **Steps (order matters):**
  1. Checkout
  2. Setup Python 3.14
  3. `pip install -e ".[dev]"`
  4. `pytest -v`
  5. `pyinstaller epo-parser.spec --noconfirm`
  6. Smoke: `dist/epo-parser.exe --help` (expect exit 0)
  7. Log size: PowerShell line printing `epo-parser.exe` size in MB (for PRD Open Question #1)
  8. `actions/upload-artifact@v4` — name e.g. `epo-parser-windows`, path `dist/epo-parser.exe`, retention per GHA defaults (or 30 days if configurable inline)

- Workflow name visible in Actions tab (e.g. `CI`).

#### 2. AGENTS.md CI note (optional one-line)

**File**: `AGENTS.md`

**Intent**: Document that Windows `.exe` builds happen in GHA, not locally on macOS.

**Contract**: Under build/test commands, note push-to-`main` triggers CI and artifact download path — one sentence, no README rewrite.

### Success Criteria:

#### Automated Verification:

- Workflow YAML is valid (no syntax errors; paths match repo layout)
- `pytest -v` passes locally before first push

#### Manual Verification:

- Push to `main` (or workflow_dispatch if temporarily added for bootstrap) produces green run
- Artifact `epo-parser-windows` contains `epo-parser.exe`
- Log shows `--help` output and file size in MB

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Size Reporting & S-05 Handoff

### Overview

Make CI size visible for PRD decision-making and document what S-05 must finish (releases, real Windows QA, optional signing).

### Changes Required:

#### 1. Change notes

**File**: `context/changes/pyinstaller-windows-build/change.md`

**Intent**: Record first observed `.exe` size from CI and handoff items for S-05.

**Contract**: Under `## Notes`, after first green CI run: paste size in MB, date, and link to the Actions run. Note that hard MB limit remains PRD Open Question #1 for user/IT LP.

#### 2. S-05 cross-reference

**File**: `context/changes/windows-portable-delivery/change.md`

**Intent**: Unblock downstream slice with explicit F-02 prerequisite satisfied.

**Contract**: Add one line under Notes: F-02 artifact available; S-05 adds LP manual verification, optional GitHub Release, and PRD size limit decision.

### Success Criteria:

#### Automated Verification:

- N/A (documentation phase)

#### Manual Verification:

- First CI run size recorded in F-02 change notes
- S-05 change notes reference F-02 artifact path
- Team agrees whether logged size is within PRD target (≤ 80 MB) or needs slimming in S-05

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Testing Strategy

### Unit Tests:

- Existing `pytest` suite unchanged — CI runs full suite before build
- No new unit tests required for spec/workflow in F-02 (infrastructure slice)

### Integration Tests:

- CI smoke: `epo-parser.exe --help` on built artifact
- Full XML→PDF via `.exe` deferred to S-05 manual / optional CI enhancement

### Manual Testing Steps:

1. Trigger CI (push to `main` or temporary `workflow_dispatch` for first bootstrap).
2. Download artifact from Actions run → verify single `epo-parser.exe` file.
3. (Optional, Windows machine) Run `--help` locally from downloaded artifact.
4. Record size from CI log in `change.md` Notes.

## Performance Considerations

- One-file PyInstaller adds startup unpack time — acceptable per PRD NFR; not measured in F-02.
- First build establishes baseline `.exe` size; if >> 80 MB, S-05 may exclude unused modules or revisit `collect_all` scope.

## Migration Notes

No data migration. Developers on macOS continue using `python main.py` / `pytest`; Windows `.exe` is CI-produced only until S-05 defines release distribution.

## References

- Roadmap F-02: `context/foundation/roadmap.md` (L97–108)
- PRD NFR + Open Question #1: `context/foundation/prd.md` (L70–72, L94–96)
- Tech stack: `context/foundation/tech-stack.md`
- Bootstrap CI hints: `context/changes/bootstrap-verification/verification.md`
- Font bundling: `pdf/renderer.py` (L19)
- Deferred Windows QA: `context/changes/directory-batch-run/change.md` (Notes)

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands.

### Phase 1: PyInstaller Spec & Dev Dependencies

#### Automated

- [x] 1.1 `pip install -e ".[dev]"` succeeds with `pyinstaller` importable — 030ab6a
- [x] 1.2 `pytest -v` still passes (no runtime behavior change) — 030ab6a

#### Manual

- [x] 1.3 Spec file reviewed: font in `datas`, `main.py` entry, onefile console mode — 030ab6a

### Phase 2: GitHub Actions CI Workflow

#### Automated

- [x] 2.1 Workflow YAML is valid (paths match repo layout)
- [x] 2.2 `pytest -v` passes locally before first push

#### Manual

- [ ] 2.3 Push to `main` produces green CI run with artifact
- [ ] 2.4 Log shows `--help` smoke output and `.exe` size in MB

### Phase 3: Size Reporting & S-05 Handoff

#### Manual

- [ ] 3.1 First CI size recorded in F-02 `change.md` Notes
- [ ] 3.2 S-05 `change.md` notes F-02 artifact available
- [ ] 3.3 Team reviews size vs PRD ≤ 80 MB target
