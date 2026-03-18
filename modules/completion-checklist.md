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

## Output Discipline

Never dump raw CLI output into context. Always redirect to a temp file and extract only the summary.

Agents in team dispatch run sequentially under the director. If worktree-based parallel execution is adopted in the future, temp files must be namespaced per-agent (e.g., `/tmp/cc_test_<role>.log`).

### Commands

Tests (Python):
```bash
pytest tests/ > /tmp/cc_test.log 2>&1
tail -n 3 /tmp/cc_test.log
```

Tests (JS/TS):
```bash
npx vitest run > /tmp/cc_test.log 2>&1
tail -n 3 /tmp/cc_test.log
```

Lint (Python):
```bash
ruff check . > /tmp/cc_lint.log 2>&1
grep -cE "(error|warning)" /tmp/cc_lint.log || echo "0 issues"
```

Lint (JS/TS):
```bash
npx eslint . > /tmp/cc_lint.log 2>&1
tail -n 3 /tmp/cc_lint.log
```

Prettier (frontend only):
```bash
npx prettier --check "src/**/*.{ts,tsx}" > /tmp/cc_prettier.log 2>&1
tail -n 1 /tmp/cc_prettier.log
```

Secrets check:
```bash
git diff --cached --stat
```
(stat only -- never full diff in context)

## Evidence Format

When reporting completion, include this exact structure with summary output from redirected logs:
```
Tests: [X passed, Y failed] (from tail of log)
Lint: [clean / N errors] (from grep count)
Prettier: [formatted / N files need formatting]
Mission match: [yes/no -- explain if no]
Secrets: [clean -- stat-only diff reviewed]
No regressions: [existing tests still pass -- from tail of log]
```

## Connections
- Used by: ALL agents (always included)
- Enforced by: pre-commit hook (Prettier, Ruff), task-completion-gate hook
- Tags: #enforcement #checklist #universal
