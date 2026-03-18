# Planned Feature Task

Type: Non-trivial (3+ steps, multi-file)
Exercises: Plan mode, plan-review-gate, completion checklist, retrospective

## Task

Add a new read-only API endpoint that returns aggregate statistics for support tickets scoped to the authenticated user's company. The endpoint returns total ticket count, open/closed breakdown, and counts by category.

## Target Files

- `appendix_k/apps/support/views.py` -- add `SupportTicketStatsView` class
- `appendix_k/apps/support/serializers.py` -- add `SupportTicketStatsSerializer` (optional, can use Response directly)
- `appendix_k/apps/support/urls.py` -- add route for stats endpoint
- `appendix_k/apps/support/tests.py` -- add test methods for new endpoint

## API Contract

- **URL:** `GET /api/v1/support/tickets/stats/`
- **Authentication:** Required (IsAuthenticated)
- **Scoping:** Company-scoped via TenantViewMixin
- **Response (200):**
  ```json
  {
    "total_tickets": 5,
    "open_tickets": 3,
    "closed_tickets": 2,
    "by_category": {
      "bug_report": 2,
      "feature_request": 1,
      "compliance_question": 2
    }
  }
  ```

## Acceptance Criteria

- New `SupportTicketStatsView` using TenantViewMixin + APIView (or RetrieveAPIView)
- Endpoint returns correct JSON shape with accurate counts
- Company-scoped: only counts tickets belonging to the authenticated user's company
- At least 2 new test methods:
  - `test_stats_endpoint_returns_200` -- authenticated request returns 200
  - `test_stats_returns_correct_counts` -- verify counts match created test data
- `ruff check apps/support/` clean
- `pytest apps/support/tests.py -v` passes all tests (existing + new)
- plan-review-gate fires before implementation begins

## Expected Agent Behavior

- Agent enters plan mode (3+ steps: view, URL, tests)
- plan-review-gate fires and blocks until Plan review agent dispatched
- Execution follows the plan's checkable items
- Completion checklist passes with redirect-and-grep evidence
- retrospective-gate fires after task completion

## Metrics to Record

- hook_block_count (expected: >=1 for plan-review-gate)
- test_pass_rate (expected: passed_first_try)
- tool_calls
- time_to_completion
- context_tokens
- session_cost (if proxy running)
- plan_quality [1-5] (human-evaluated)
- rework_needed [none/minor/significant] (human-evaluated)
