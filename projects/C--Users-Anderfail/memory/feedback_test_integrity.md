---
name: feedback_test_integrity
description: Tests must reflect real behavior — never modify a test to force it to pass; fix the site if a test reveals a real bug
type: feedback
---

Tests must cover actual use cases and reflect real application behavior. When a test fails:
- If the test was written poorly → fix the test, rerun
- If the test reveals a real site bug → fix the site, NOT the test

Never change a test just to force it to pass. This is 100% unacceptable.

**Why:** The user sees tests as a source of truth about whether the application works correctly. Modifying tests to match broken behavior defeats the entire purpose of testing and hides real bugs.

**How to apply:**
- When a failing test exposes a genuine bug, treat it as a site fix task, not a test fix
- When writing new tests, model real user scenarios (E2E flows, mobile/desktop, online/offline)
- During the Phase 5 test overhaul, audit ALL existing tests against this standard — any test that passes by testing the wrong thing needs to be rewritten
- This applies retroactively: existing tests that were written to pass rather than to validate behavior must be identified and corrected

## Connections
- Related: [[feedback_no_lower_thresholds]], [[run-tests]]
- Tags: #feedback #testing
