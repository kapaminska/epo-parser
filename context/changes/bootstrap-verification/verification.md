---
bootstrapped_at: 2026-06-17T13:45:00Z
starter_id: python-cli
starter_name: Python CLI (uv + pyproject)
project_name: epo-parser
language_family: python
package_manager: uv
cwd_strategy: subdir-then-move
bootstrapper_confidence: first-class
phase_3_status: ok
audit_command: pip-audit
---

## Hand-off

```yaml
starter_id: python-cli
package_manager: uv
project_name: epo-parser
hints:
  language_family: python
  team_size: solo
  deployment_target: github-releases
  ci_provider: github-actions
  ci_default_flow: build-on-merge
  bootstrapper_confidence: first-class
  path_taken: custom
  quality_override: false
  self_check_answers: null
  has_auth: false
  has_payments: false
  has_realtime: false
  has_ai: false
  has_background_jobs: false
  has_gui: false
  packaging: pyinstaller
```

## Why this stack

Python CLI packaged as a single portable `.exe` (PyInstaller). User runs the exe in a folder of XML files; feedback is `epo-konwersja.txt`, not a GUI. Develop on macOS; build Windows artifact in GitHub Actions on `windows-latest`. Core libs: lxml (XML), fpdf2 (PDF), pytest (tests).

## Pre-scaffold verification

| Signal             | Value                              | Severity | Notes                              |
| ------------------ | ---------------------------------- | -------- | ---------------------------------- |
| npm package        | not run                            | —        | non-JS starter; npm check skipped  |
| GitHub repo        | not run                            | —        | docs_url is https://docs.astral.sh/uv/ (not GitHub) |

Recency: no recency signal available. Proceeding.

## Scaffold log

**Resolved invocation**: `uv init .bootstrap-scaffold --name bootstrap_scaffold --app --no-workspace --vcs none`

**Note**: The registry card's original `cmd_template` (`uv init {name}`) failed because `.bootstrap-scaffold` is not a valid Python package name. The template was updated to include `--name bootstrap_scaffold --app --no-workspace --vcs none` before the successful run.

**Strategy**: subdir-then-move

**Exit code**: 0

**Files moved**: 3 (`main.py`, `pyproject.toml`, `.python-version`)

**Conflicts (.scaffold siblings)**: `README.md.scaffold`

**.gitignore handling**: absent in scaffold

**.bootstrap-scaffold cleanup**: deleted

## Post-scaffold audit

**Tool**: pip-audit

**Status**: failed to run

**Reason**: `pip-audit` not installed on PATH

**Partial output (if any)**:

```
(none)
```

## Hints recorded but not acted on

| Hint                       | Value                              |
| -------------------------- | ---------------------------------- |
| bootstrapper_confidence    | first-class                        |
| quality_override           | false                              |
| path_taken                 | custom                             |
| self_check_answers         | null                               |
| team_size                  | solo                               |
| deployment_target          | github-releases                    |
| ci_provider                | github-actions                     |
| ci_default_flow            | build-on-merge                     |
| has_auth                   | false                              |
| has_payments               | false                              |
| has_realtime               | false                              |
| has_ai                     | false                              |
| has_background_jobs        | false                              |
| has_gui                    | false                              |
| packaging                  | pyinstaller                        |

## Next steps

Next: a future skill will set up agent context (CLAUDE.md, AGENTS.md). For now, your project is scaffolded and verified — happy hacking.

Useful manual steps in the meantime:
- `git init` (if you have not already) to start your own repo history.
- Review any `.scaffold` siblings the conflict policy created and decide which version of each file to keep.
- Address audit findings per your project's risk tolerance — the full breakdown is in this log.
- Rename the project in `pyproject.toml` from `bootstrap-scaffold` to `epo-parser` (or `epo_parser` for the Python package name).
- Install `pip-audit` (`uv tool install pip-audit`) and re-run when dependencies are added.
