---
name: workflow-protocol
description: Use for ALL task execution — governs assessment, planning, execution, team dispatch, and retrospective
---

## The Six Rules

These six rules govern ALL task execution. They are the highest-priority content in this skill — when context is limited, these rules must survive. Every decision, every agent dispatch, every completion report flows through these rules. Violating any rule is a process failure that must be captured in the retrospective.

1. **Plan non-trivial work.** Any task with 3 or more steps, any architectural decision, any multi-file change → enter plan mode. Write a plan with checkable items before writing any code. Trivial tasks (single file edit, quick lookup, fewer than 3 steps) may execute directly, but still require the completion checklist. When in doubt, plan — the cost of over-planning is a few minutes of thought; the cost of under-planning is rework, missed edge cases, and broken builds.

2. **Review every plan.** Before calling ExitPlanMode, dispatch a Plan review agent. The review must check for: factual errors in the plan, phantom work items that reference nonexistent code or APIs, missing dependencies between steps, thin margins on complex steps, and unrealistic scope estimates. Incorporate all issues from the review into the plan before presenting it to the user. A plan that has not been reviewed is not a plan — it is a guess.

3. **Split by context, not role.** When deciding whether to use multiple agents, ask "what context does this agent need?" not "what role does this agent play?" A "backend agent" and "testing agent" working on the same Django app is a role split — both need the same models, signals, and views, so splitting them creates handoff risk for zero benefit. A backend agent and a frontend agent working on different sides of an API contract is a context split — each has genuinely isolated context and can work independently. The unit of splitting is the context boundary, never the job title.

4. **Compose, don't assume.** Every dispatched agent receives its knowledge modules explicitly listed in the dispatch prompt. Never assume an agent "knows" something because a previous agent knew it. The director (the main conversation when coordinating a team — see Phase 2) must consult `~/.claude/modules/README.md` for the composition mapping and include every module the agent will need. If an agent lacks a critical module, it will make incorrect assumptions. If an agent receives irrelevant modules, it wastes context window on noise. Both are failures — compose deliberately.

5. **Never declare done without proof.** Every task completion must include quoted evidence: test output with pass/fail counts, linter output showing clean or listing specific errors fixed, prettier verification for frontend files. The phrase "tests pass" without pasted output is never acceptable. The phrase "lint is clean" without pasted output is never acceptable. If you cannot produce the evidence, the task is not complete. This rule applies to every agent, every task, every time — no exceptions for "simple" changes.

6. **Retrospect every plan.** After completing any planned task, run the mandatory 3-layer retrospective: work review (what happened), process review (did the process work), and system evolution (should the system change). This is not optional, not deferrable, and not skippable for "straightforward" plans. The retrospective is where the system learns. Skipping it means repeating mistakes.

## Completion Checklist

This checklist is MANDATORY for every task, every agent, every time. No exceptions. This is the embedded, always-available reference that enforces Rule 5. Every agent dispatched by the director receives this checklist as part of its prompt via the `completion-checklist` module.

### Before Declaring Any Task Complete

- [ ] **Tests passing**: Run the test suite. Quote the output. "Tests pass" without output is NOT acceptable.
  - Python: `pytest <relevant_test_file> -v` — quote pass/fail counts
  - JS/TS: `npm test` or `npx vitest run <file>` — quote pass/fail counts
  - If no tests exist for the changed code, write them first. Do not skip tests to save time.
  - If the test suite has unrelated failures, note them explicitly and confirm your changes did not cause them.
- [ ] **Lint clean**: Run the linter on all changed files. Quote the output.
  - Python: `ruff check <files>` — must show no errors
  - JS/TS: `npx eslint <files>` — must show no errors
  - Fix all linting errors before declaring complete. Do not suppress warnings without justification.
- [ ] **Prettier run** (frontend files only): Run Prettier on all changed `.ts`, `.tsx`, `.css`, `.json` files.
  - `npx prettier --write <files>`
  - Then verify: `npx prettier --check <files>`
  - This step is mandatory for every frontend file modification, no matter how small the change.
- [ ] **Changes match mission**: Compare what you built against the mission statement or task description. Does it do what was asked? Nothing more, nothing less. Scope creep is a failure. Missing requirements are a failure. Both must be caught here.
- [ ] **No secrets**: Review the diff. No API keys, passwords, .env content, or credentials may be committed. Check for hardcoded URLs with tokens, database connection strings, and any other sensitive values.
- [ ] **No regressions**: If you modified existing code, verify existing tests still pass. Run the full relevant test suite, not just the new tests. A change that adds a feature but breaks existing functionality is not complete.

### Evidence Format

When reporting completion, include this exact structure with real output pasted in:

```
Tests: [X passed, Y failed] (paste output)
Lint: [clean / N errors] (paste output)
Prettier: [formatted / N files]
Mission match: [yes/no — explain if no]
Secrets: [clean]
```

This format is non-negotiable. It allows the director (or the user) to verify completion at a glance without re-running tools. If any field shows a failure, the task is not complete — fix the issue and re-run the checklist.

## Phase 1: Assessment & Planning

Every task begins with assessment. Before writing any code, before dispatching any agent, answer two questions in order.

### Decision 1 — Does This Need a Plan?

Evaluate the task against these criteria:

- **Trivial** (execute directly): Single file edit, quick lookup, fewer than 3 steps, no architectural decisions, no ambiguity about approach. Examples: fixing a typo, adding a log statement, looking up a function signature, renaming a variable. Even trivial tasks require the completion checklist — tests must pass, lint must be clean.

- **Non-trivial** (enter plan mode): 3 or more steps, any architectural decision (new model, new signal, new API endpoint, state machine change), multi-file changes with dependencies between them, any task where the approach is not immediately obvious. Enter plan mode, write a plan with checkable items, dispatch the Plan review agent to check for factual errors and missing dependencies, then present the reviewed plan for user approval.

**Ambiguity rule:** When uncertain whether a task is trivial or non-trivial, default to non-trivial. The cost of over-planning is a few minutes spent thinking through the approach. The cost of under-planning is missed edge cases, rework, broken integrations, and lost user trust. Over-planning has a low ceiling of waste; under-planning has an unbounded ceiling of damage.

**Escalation rule:** If a trivial task reveals unexpected complexity during execution — more files affected than anticipated, architectural decisions required, or ambiguity about the correct approach — stop execution, enter plan mode, and re-assess as non-trivial. Do not push through a task that has outgrown its trivial assessment.

### Decision 2 — Does This Need a Team?

This decision is only evaluated for planned tasks. Trivial tasks are always single-agent by definition.

- **Single-agent** (default): The task's context fits within one agent's working memory. All files, models, signals, views, and tests that the agent needs to reason about can be loaded together without exceeding useful context limits. This is the default — most tasks should be single-agent.

- **Context team**: The task involves 2 or more genuinely isolated context boundaries where the agents can work independently, communicating only through well-defined interfaces (API contracts, shared schemas, event formats). The director coordinates but does not write code.

**Context isolation test — the single decisive question:**

```
"Can Agent A complete its work without knowing what Agent B is doing?"
  YES → Split into separate agents (genuinely isolated)
  NO  → Keep in one agent (overlapping context = handoff risk)
```

The threshold is context isolation, not step count. A 5-step all-backend task stays single-agent because every step needs the same models and signals. A 3-step backend+frontend task gets a team because the backend agent only needs to know the API contract, not the React component tree, and vice versa.

Splitting agents that share context is actively harmful. It creates handoff overhead, risks inconsistency when one agent changes something the other depends on, and forces the director to mediate communications that would have been implicit in a single agent's working memory. Never split for parallelism alone — split only for genuine context isolation.

### Calibration Examples

These five examples establish the decision boundary. Study the reasoning column — it shows the context isolation test applied to real scenarios.

| Task | Decision | Reasoning |
|---|---|---|
| Add new compliance check (model + signal + view + test) | Single-agent | All backend Django context. Signal handler needs to know the model and the view needs the signal — deeply overlapping. Splitting would force one agent to guess what the other built. |
| Add compliance check + dashboard widget displaying results | Team (backend + frontend) | Backend agent builds the check end-to-end including the API endpoint. Frontend agent builds the widget consuming the API. Neither needs the other's implementation details — only the API contract (URL, request/response shape). |
| Refactor operator qualification state machine | Single-agent | All interconnected signal chains where each transition depends on the previous state. Splitting would lose the state transition context that makes the refactor coherent. |
| Django view renders a template with inline JS | Single-agent | Template is part of the Django context — the view passes context variables that the template consumes, and the inline JS reads those variables. Splitting at the template boundary creates a handoff for tightly coupled code with no clean interface between the halves. |
| New feature: approval workflow (backend API + React approval page + email notifications) | Team (backend + frontend) | Backend builds API endpoints, Celery email tasks, and model changes. Frontend builds the React approval page. The Celery task is backend context (triggered by model save, not by the frontend). Clean API boundary between the two agents. |

## Phase 2: Execution

### Single-Agent Mode

When a task is assessed as single-agent (whether trivial or planned), the main conversation implements directly:

- Follow domain skills as needed (compliance-checks, operator-qualification-lifecycle, etc.)
- For planned tasks, track progress against the plan's checkable items, marking each complete with evidence
- Run tests and linting on each changed file before moving to the next task item — do not batch quality checks to the end, as early failures are cheaper to fix
- Upon completing all items, run the full completion checklist and present evidence
- For planned tasks, proceed to Phase 3 (retrospective). For trivial tasks, the completion checklist is sufficient.

### Director + Team Mode

When a task is assessed as needing a context team, the main conversation becomes the director. The director coordinates but does NOT write code — all implementation is done by dispatched agents.

**Agent dispatch protocol — for each context-scoped agent, the director must:**

1. **Define a one-sentence mission** that clearly states what the agent must deliver. The mission must be specific enough that the agent can evaluate its own success. Bad: "Handle the backend." Good: "Implement the compliance check API endpoint at /api/v1/checks/ with GET (list) and POST (create) methods, returning JSON matching the ComplianceCheckSerializer schema."

2. **Identify knowledge modules** to compose into the agent's prompt by consulting `~/.claude/modules/README.md` for the composition mapping. Each module adds domain-specific knowledge the agent needs. Include every relevant module; exclude irrelevant ones. A backend compliance agent might need: compliance-audit, verification, completion-checklist. A frontend agent might need: frontend-architecture, completion-checklist.

3. **Set explicit scope boundaries** so the agent knows exactly what it owns and what it must not touch. Format: "You are responsible for X. Do NOT touch Y." This prevents agents from making well-intentioned changes outside their context that conflict with another agent's work.

4. **Set concrete deliverables and acceptance criteria** that the director can verify without re-implementing the work. Acceptance criteria should be testable: "New check model has fields X, Y, Z. POST endpoint returns 201 with check ID. Existing compliance tests still pass. Ruff clean on all changed files."

5. **Always include the `completion-checklist` module** in every agent's prompt. This is non-negotiable — it enforces Rule 5 at the agent level.

6. **Dispatch the agent** and save a checkpoint (see Director State Checkpoint section) capturing the dispatch state.

**Post-dispatch director responsibilities:**

- Review each agent's output against acceptance criteria. Do not rubber-stamp — verify the evidence in the completion report.
- If an agent's output has conflicts with another agent's work, the director resolves the conflict and re-dispatches the affected agent with updated context explaining what changed and why.
- If an agent's output is insufficient (missing deliverables, failing tests, incomplete evidence), provide specific feedback and re-dispatch. Maximum 3 retries per agent — if the agent cannot succeed after 3 attempts, escalate to the user with a summary of what was attempted and what failed.

### Peer Communication (Director-Mediated)

Agents never communicate directly. All information flows through the director:

- Agent A reports a finding that affects Agent B's scope → Director evaluates the impact → If the finding changes Agent B's requirements, the Director updates Agent B's context and mission, then re-dispatches Agent B with the new information explicitly stated
- Agent A needs information from Agent B's domain → Director retrieves it from Agent B's deliverable (via `deliverable_search`) and provides it to Agent A
- All state changes, all new context, all scope adjustments flow through the director. This ensures the director always has a complete picture of the system state and can detect conflicts before they become merge problems.

## Common Patterns Reference

Suggested sequences for common task types. These are starting points, not mandates — the director adapts based on the actual task context, the modules available, and the complexity discovered during planning.

| Pattern | Suggested Sequence |
|---|---|
| Bug fix | Reproduce the bug with a failing test → Fix the code → Review with verification and security modules to confirm no regression or exposure |
| Feature (single-context) | Design the approach → Implement and test in a single agent, pulling in the architecture module if structural decisions are needed |
| Feature (multi-context) | Design the approach and define API contracts → Dispatch backend agent and frontend agent in parallel → Integration review once both deliver |
| Compliance change | Audit the impact across existing checks and signals → Implement with the compliance-audit module → Run full verification suite |
| Architecture decision | Evaluate options using the architecture module → Write an ADR documenting the decision and rationale → Implement the chosen approach |

When a task does not cleanly fit a pattern, the director constructs a custom sequence using the same principles: isolate context, compose modules, set acceptance criteria, verify with evidence.

## Director State Checkpoint

The director saves a checkpoint via `checkpoint_save` at two critical moments: before each agent dispatch and before context compaction. This checkpoint captures the full coordination state so the director can recover after compaction without losing track of in-flight work.

Checkpoint schema:

```json
{
  "phase": "execution",
  "mode": "director-team",
  "plan_task_ids": ["1", "2", "3", "4"],
  "agents_dispatched": [
    {
      "agent_id": "abc123",
      "mission": "Implement backend compliance check",
      "modules": ["compliance-audit", "verification", "completion-checklist"],
      "scope": "apps/compliance/ and apps/operators/signals.py",
      "acceptance_criteria": "New check passes, existing tests pass, ruff clean",
      "status": "in_flight",
      "retry_count": 0
    }
  ],
  "pending_agents": [],
  "conflicts_resolved": [],
  "retrospective_completed": false
}
```

**Recovery after compaction:** Subagent results are returned to the conversation regardless of compaction — they arrive as tool results that persist. After compaction, the director calls `checkpoint_restore` to recover the coordination state, then cross-references the restored checkpoint against any agent results that have arrived. The checkpoint tells the director which agents were in-flight, what their acceptance criteria were, and what work remains. Without the checkpoint, the director would not know what to expect or how to evaluate returning results.

**Checkpoint hygiene:** Update the checkpoint after every state change — agent completion, conflict resolution, re-dispatch, scope change. A stale checkpoint after compaction is worse than no checkpoint because it provides false confidence about the system state.

## Phase 3: Completion & Retrospective

### Trivial Tasks (No Plan)

For tasks that were assessed as trivial and executed directly without a plan:

- Run the full completion checklist: tests pass (with quoted output), lint clean (with quoted output), prettier run (for frontend files), changes match the request, no secrets in the diff, no regressions in existing tests
- No formal retrospective is required unless: a user correction occurred during the task, something unexpected went wrong, or a hook fired that should not have. In these cases, run a lightweight retrospective focusing on what went wrong and whether it should become a feedback memory.

### Planned Tasks — Mandatory 3-Layer Retrospective

Every planned task — whether single-agent or director+team — requires this full retrospective after the completion checklist passes. This is where the system learns from experience. Skipping the retrospective is a Rule 6 violation.

#### Layer 1 — Work Review

Focus: what actually happened during this task.

- What files changed? What architectural decisions were made? Were any decisions forced by unexpected constraints?
- Were any of the Six Rules violated during execution? Which hooks fired, and were they appropriate?
- Did any tasks get marked complete prematurely? (Check: was there a completion report with full evidence, or was the task marked done informally?)
- Were any user corrections received during execution? Each correction is a signal that the plan or the assessment missed something.

#### Layer 2 — Process Review

Focus: did the workflow protocol serve this task well.

- Did any hard hooks trigger during execution? If yes, this indicates an upstream process failure — the plan should have caught whatever the hook caught. Investigate: why did the plan miss it? Should the planning phase be more thorough for this type of task?
- For team tasks: did the context splitting work? Did handoffs between agents lose information? Did any agent need context that it was not given? Did any agent receive modules it did not need?
- Were the right knowledge modules composed for each agent? If an agent struggled because it lacked domain knowledge, the module composition was wrong. If an agent wasted context on irrelevant information, the composition was wasteful.
- Did the trivial/planned threshold feel right? Did the single-agent/team threshold feel right? If the task was assessed as trivial but turned out to be complex, the assessment criteria may need calibration.

#### Layer 3 — System Evolution

Focus: should the system itself change based on what we learned.

**Always items (run every retrospective):**

- **Memory:** Did this task reveal new feedback worth recording, new anti-patterns to avoid, or new navigation entries for the codebase? If yes, propose additions to the appropriate memory files.
- **Decision journal:** Were any architectural decisions made that should be recorded in the project's decision journal? New models, new signal patterns, new API designs, changes to state machines — these all warrant ADR entries.
- **Kanban update:** Move completed cards to done. Add new improvement cards for any issues discovered during the retrospective — technical debt found, process gaps identified, module gaps noticed.
- **Modules:** Did any agent lack needed knowledge that should be in a module? Did any agent receive a module full of irrelevant noise that should be trimmed? Propose specific module updates with rationale.

**Periodic items (every 5th retrospective, or triggered on-demand via /vault-health):**

- **Hooks:** Should a new pre-commit or pre-push hook be added based on recurring issues? Should an existing hook's threshold or scope be adjusted?
- **Skills:** Should any domain skill be amended based on new patterns learned or mistakes made?
- **Director protocol:** Should the composition logic, the context isolation test, or the dispatch protocol change?
- **Vault hygiene:** Run orphan detection on the knowledge vault — find broken links, stale references, modules that are never composed, memory entries that are outdated. Check connection density between vault nodes and token budgets for oversized modules.
- **Inbox processing:** Categorize any raw ideas that accumulated during the task into their proper vault locations — feedback becomes memory, patterns become module updates, decisions become ADR entries.
- **Canvas update:** If structural changes to the codebase were detected (new apps, new services, changed dependencies), regenerate the system-architecture.canvas to reflect the current state.

**Exception handling:** A catastrophic failure or system incident triggers ALL items — both always and periodic — regardless of where the task falls in the retrospective cadence. System incidents demand full audit.

### Handling Outcomes

- **Catastrophic failures** (broken builds, data loss, security exposure, production incidents) → saved as "system incident" feedback memory with high priority. These memories persist and influence future planning to prevent recurrence.

- **Exceptional successes** (unusually clean execution, novel patterns that worked well, efficient context splits) → saved as "proven pattern" to be formalized into the protocol or added to a module as a recommended approach.

- **All Layer 3 proposals** require explicit user approval before being implemented. The retrospective proposes changes; the user decides. Declined proposals are recorded in `declined-proposals.md` with the reason for declining, so the system does not re-propose the same change.

- **Hook fires during retrospective check:** If a hook fired during execution, Layer 2 must capture the full chain: which hook fired, what it caught, why the earlier process steps (planning, assessment, or the agent itself) failed to catch it first, and what systemic fix would prevent the hook from needing to fire for this class of issue in the future.

- **User correction received (any task, including trivial):** Any user correction triggers a lightweight retrospective even for trivial tasks. Ask: should this correction become a feedback memory so it is not repeated? Is this a repeat of a previous correction? If it is a repeat, escalate to a system incident — the system failed to learn from the first correction and needs a structural fix, not just a memory entry.

## Hermes-Bridge Quick Reference

These tools manage session context and inter-agent deliverables. Use them for checkpoint persistence and agent coordination.

- `session_search(query)` — search past sessions for relevant context, prior decisions, and previous approaches to similar tasks
- `checkpoint_save(session_id, summary, ...)` — save the director's coordination state before context compaction or agent dispatch so it can be recovered
- `checkpoint_restore(session_id?)` — recover the director's coordination state after compaction, returning the last saved checkpoint
- `deliverable_save(pipeline_id, agent_role, ...)` — save an agent's output as a deliverable that downstream agents or the director can consume
- `deliverable_search(pipeline_id, for_consumer)` — retrieve a saved deliverable, typically used by the director to pass one agent's output to another or to review agent work
- `session_index(session_id, jsonl_path)` — manually re-index a session transcript (rarely needed; used for repair or retroactive indexing)
