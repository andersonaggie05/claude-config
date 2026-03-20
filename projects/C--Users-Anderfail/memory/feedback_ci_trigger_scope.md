---
name: feedback_ci_trigger_scope
description: Appendix K CI only triggers on push to main or PRs targeting main — not feature branch pushes
type: feedback
---

CI workflow (`.github/workflows/ci.yml`) only triggers on push to `main` (and a few hardcoded branches) or pull_request targeting `main`. Pushing to a feature branch alone will not trigger CI.

**Why:** During baseline measurement task (2026-03-18), pushed to `baseline/measurements` and waited for CI — nothing happened. Had to create a PR to get CI feedback.

**How to apply:** After pushing a feature branch, immediately create a PR if CI validation is needed. Don't wait for a CI run that won't come.
