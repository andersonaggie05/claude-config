---
name: feedback_lint_baseline
description: Run full lint suite as first commit on feature branches to separate formatting from feature work
type: feedback
---

When starting a feature branch, run the full lint suite (ruff check --fix + ruff format for Python, npm run format for frontend) and commit any formatting fixes as the FIRST commit. This separates "cleanup" noise from actual feature changes in the PR diff.

**Why:** During Phase 3 PWA, the Task 15 verification pass reformatted 20+ unrelated files across the codebase, polluting the PR diff with formatting noise mixed into feature commits. This makes code review harder and obscures what actually changed.

**How to apply:**
- After creating a feature branch, run: `ruff check --fix apps/ && ruff format apps/` + `cd frontend && npm run format`
- Commit any changes as "Normalize formatting before feature work"
- Then proceed with feature development on a clean baseline
- This ensures subsequent commits only contain intentional changes

## Connections
- Related: [[feedback_thoroughness]]
- Tags: #feedback #workflow #linting
