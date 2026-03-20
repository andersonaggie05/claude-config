---
name: feedback_venv_tooling
description: Ruff and pytest may not be installed in appendix_k venv; use .venv/Scripts/ path directly
type: feedback
---

Ruff and pytest are not always installed in the appendix_k venv. Don't rely on PATH or `rtk ruff` — use `.venv/Scripts/ruff.exe` and `.venv/Scripts/python.exe -m pytest` directly.

**Why:** Discovered during baseline measurement task (2026-03-18) — `rtk ruff check` failed because ruff wasn't on PATH, and `python -m pytest` failed with "No module named pytest". Cost 3 extra tool calls to diagnose and install.

**How to apply:** When running lint or tests in appendix_k, always use the full `.venv/Scripts/` path. If a tool is missing, install it before proceeding rather than trying alternate invocations.
