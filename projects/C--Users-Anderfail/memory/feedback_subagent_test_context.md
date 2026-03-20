---
name: feedback_subagent_test_context
description: When dispatching subagents to modify files, include tests that assert invariants about those files
type: feedback
---

When dispatching subagents to modify files, include in the prompt any existing tests that enforce invariants about those files.

**Why:** During QAQC V3 Release 4, three subagents modified HTML templates in parallel. One agent added `innerHTML` for tab caching, which broke an existing test asserting "no innerHTML usage" in the repair scorecard template. The agent had no way to know about that test constraint.

**How to apply:** Before dispatching file-modification subagents, grep for tests that reference those files. Include the test names and their assertions in the subagent prompt so they can accommodate or flag conflicts. Alternatively, run tests immediately after subagent changes before proceeding.
