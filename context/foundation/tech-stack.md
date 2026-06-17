---
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
---

## Why this stack

Python CLI packaged as a single portable `.exe` (PyInstaller). User runs the exe in a folder of XML files; feedback is `epo-konwersja.txt`, not a GUI. Develop on macOS; build Windows artifact in GitHub Actions on `windows-latest`. Core libs: lxml (XML), fpdf2 (PDF), pytest (tests).
