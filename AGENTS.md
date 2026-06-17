# Repository Guidelines

EPO Parser is a Python CLI desktop app (PyInstaller `.exe`) that converts Polish Post EPO XML files into readable PDFs for Lasów Państwowych. No GUI — user runs the exe in a folder of XML files; feedback is `epo-konwersja.txt`. Product requirements: @context/foundation/prd.md; stack: @context/foundation/tech-stack.md.

## Hard Rules

- Never overwrite an existing output PDF or summary `.txt`; on name conflict append a suffix like ` (2)` per @context/foundation/prd.md.
- All XML→PDF processing stays local—no outbound network calls.
- Do not write to `context/archive/`; archived changes are immutable. Open new work with `/10x-new`.
- Keep change-scoped artifacts in `context/changes/<change-id>/`; edit foundation docs in place at `context/foundation/` per @context/foundation/README.md.

## Build, Test, and Development Commands

(Python project layout to be added with first implementation slice.)

- `pip install -e ".[dev]"` — install package and dev deps (once `pyproject.toml` exists).
- `pytest` — run tests (`tests/`, fixtures under `tests/fixtures/`).
- `python -m epo_parser` or `python main.py` — run locally before packaging.
- PyInstaller one-file build — via CI on `windows-latest` (see @context/foundation/tech-stack.md).

## Project Structure

- `main.py` — entry: scan cwd / CLI args, batch conversion, write summary txt.
- `parsers/` — XML source adapters (per schema).
- `domain/` — canonical EPO model, output naming rules.
- `pdf/` — canonical model → PDF.
- `tests/` — pytest; fixtures in `tests/fixtures/`.
- `context/foundation/` — PRD, tech stack, roadmap.
- `context/changes/` — active change folders.
- `ai/idea.md` — original design notes.

## Coding Style & Naming Conventions

- Python 3.11+; type hints on public APIs in `domain/`, `parsers/`, `pdf/`.
- Modules and functions: `snake_case`; test files `test_*.py`.
- Docstrings on public domain/parser/pdf APIs (see @.cursor/rules/documentation.mdc).

## Testing Guidelines

- `pytest` for parsers, domain naming rules, and integration XML → PDF on temp dirs.
- Mandatory coverage for parsers and output filename suffix logic before shipping MVP slices.
- CI: GitHub Actions (`pytest` + PyInstaller build on Windows).

## Commit & Pull Request Guidelines

Establish git convention before first push. Target Windows 10/11 portable `.exe`; develop on macOS, build Windows artifact in CI.

## Architecture Overview

- Single Python process: file I/O, XML canonicalization, PDF generation, text summary — no frontend.
- New EPO XML schemas: new adapter in `parsers/`, shared model in `domain/` (@context/foundation/prd.md).
- Deeper context: @ai/idea.md.
