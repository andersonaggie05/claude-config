---
name: Completion Checklist
description: Universal verification checklist required before any task can be declared complete
type: knowledge-module
source: New (consolidation of enforcement rules)
---

# Completion Checklist

This checklist is MANDATORY for every task, every agent, every time. No exceptions.

## Before Declaring Any Task Complete

- [ ] **Tests passing**: Run the test suite. Quote the output. "Tests pass" without output is NOT acceptable.
  - Python: `pytest <relevant_test_file> -v` — quote pass/fail counts
  - JS/TS: `npm test` or `npx vitest run <file>` — quote pass/fail counts
- [ ] **Lint clean**: Run the linter on all changed files. Quote the output.
  - Python: `ruff check <files>` — must show no errors
  - JS/TS: `npx eslint <files>` — must show no errors
- [ ] **Prettier run** (frontend files only): Run Prettier on all changed `.ts`, `.tsx`, `.css`, `.json` files.
  - `npx prettier --write <files>`
  - Then verify: `npx prettier --check <files>`
- [ ] **Changes match mission**: Compare what you built against the mission statement / task description. Does it do what was asked? Nothing more, nothing less.
- [ ] **No secrets**: Review the diff. No API keys, passwords, .env content, or credentials.
- [ ] **No regressions**: If you modified existing code, verify existing tests still pass.

## Evidence Format

When reporting completion, include:
```
Tests: [X passed, Y failed] (paste output)
Lint: [clean / N errors] (paste output)
Prettier: [formatted / N files]
Mission match: [yes/no — explain if no]
Secrets: [clean]
```

## Connections
- Used by: ALL agents (always included)
- Enforced by: pre-commit hook (Prettier, Ruff), task-completion-gate hook
- Tags: #enforcement #checklist #universal
