# Trivial Bugfix Task

Type: Trivial (single file, <3 steps)
Exercises: Trivial assessment, completion checklist, redirect-and-grep

## Task

Fix a missing type annotation in `apps/support/models.py`. The `SupportTicket.description` field (TextField) lacks an explicit type annotation. Add the appropriate type hint and verify with ruff.

## Target Files

- `appendix_k/apps/support/models.py` -- add type annotation to `description` field

## Specific Instructions

1. Open `apps/support/models.py`
2. Add a type annotation to the `description` field declaration
3. Run ruff check and fix any issues
4. Run existing tests to confirm no regressions

## Acceptance Criteria

- Type annotation added to `description` field
- `ruff check apps/support/` shows no errors
- `pytest apps/support/tests.py -v` passes all existing tests (3 test classes)
- Completion checklist satisfied with redirect-and-grep evidence

## Expected Agent Behavior

- Agent correctly classifies as trivial (no plan mode)
- Completion checklist runs with redirect-and-grep pattern
- No hook blocks (agent follows process on first pass)

## Metrics to Record

- hook_block_count (expected: 0)
- test_pass_rate (expected: passed_first_try)
- tool_calls
- time_to_completion
- context_tokens
