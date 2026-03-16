---
name: feedback_no_lower_thresholds
description: Never lower test coverage thresholds or quality gates to fix CI - write tests instead
type: feedback
---

Never lower test coverage thresholds, lint rules, or quality gates to fix CI failures. Always write tests to fill coverage gaps instead.

**Why:** The user views thresholds as a floor, not a target. Lowering them defeats the purpose of having them.

**How to apply:** When new code drops coverage below thresholds, add tests for the new code (and nearby untested code if needed) to bring coverage back above the threshold. Consider this a mandatory part of feature work, not optional polish.

## Connections
- Related: [[run-tests]], [[completion-checklist]]
- Tags: #feedback #testing
