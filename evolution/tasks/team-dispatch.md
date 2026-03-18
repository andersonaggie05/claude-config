# Team Dispatch Task

Type: Non-trivial, multi-context (requires director + team)
Exercises: Context splitting, file-level scoping, git branch checkpointing, module composition, cross-agent coordination

## Task

Add a new `ticket_escalated` alert type to the compliance system that triggers when a support ticket meets escalation criteria (category is `compliance_question` and description exceeds 500 characters). This requires both backend changes (new alert type + signal) and a frontend component to display escalated ticket alerts.

## Backend Scope (Agent 1)

**Files:**
- `appendix_k/apps/compliance/models.py` -- add `('ticket_escalated', 'Ticket Escalated')` to ALERT_TYPE_CHOICES
- `appendix_k/apps/support/signals.py` (new file) -- create `on_support_ticket_saved` signal handler
- `appendix_k/apps/support/apps.py` -- register signal in `ready()` method
- `appendix_k/apps/support/tests.py` -- add signal/alert test methods

**Acceptance Criteria:**
- New alert type choice added to ComplianceAlert model
- Signal fires on SupportTicket post_save when criteria met
- ComplianceAlert created with type `ticket_escalated`, title includes ticket subject
- 3 new test methods:
  - `test_escalated_alert_created_on_long_compliance_question`
  - `test_no_alert_for_short_tickets`
  - `test_no_alert_for_non_compliance_category`
- Ruff clean, all tests pass

## Frontend Scope (Agent 2)

**Files:**
- `appendix_k/frontend/src/components/alerts/TicketEscalatedAlert.jsx` (new) -- display component
- `appendix_k/frontend/src/components/alerts/index.js` -- export new component
- `appendix_k/frontend/src/components/alerts/__tests__/TicketEscalatedAlert.test.jsx` (new) -- component tests

**Acceptance Criteria:**
- Component renders alert with ticket subject, category, and escalation reason
- Component follows existing alert display patterns (check other alert components for reference)
- At least 2 test methods: renders correctly, displays ticket subject
- Prettier formatted, eslint clean

## API Contract Between Agents

The backend agent produces a `ComplianceAlert` with:
- `alert_type`: `"ticket_escalated"`
- `title`: `"Ticket Escalated: {ticket.subject}"`
- `description`: `"Support ticket #{ticket.id} requires review"`

The frontend agent consumes this via the existing ComplianceAlert API endpoint. No new API endpoints needed.

## Expected Agent Behavior

- Director splits into backend agent and frontend agent
- Each agent receives file-level scope (not directory-level)
- Each agent gets appropriate modules composed (backend: verification + completion-checklist; frontend: verification + completion-checklist)
- Git branches created: `task/ticket-escalated/backend` and `task/ticket-escalated/frontend`
- Director merges after acceptance criteria met
- Both agents' completion checklists pass

## Metrics to Record

- hook_block_count
- test_pass_rate
- tool_calls
- time_to_completion
- context_tokens
- session_cost (if proxy running)
- discovery_efficiency (human-evaluated)
- scope_adherence (automated: git diff vs assigned file list)
- plan_quality [1-5] (human-evaluated)
- rework_needed [none/minor/significant] (human-evaluated)
