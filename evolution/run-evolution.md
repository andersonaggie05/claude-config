# Evolution Experiment Protocol

## Purpose

Test Layer 3 system evolution proposals empirically before presenting them for user approval. This is the autoresearch pattern applied to the workflow itself: branch, apply, test, measure, keep or discard.

This is a protocol document, not a skill or module. It is read on demand by the Layer 3 retrospective when an evolution experiment is warranted. It carries zero session overhead.

## When to invoke

- After a Layer 3 retrospective generates a testable proposal
- When the user asks to test a workflow change before committing to it
- During the periodic meta-review (every 5th retrospective)

## Classifying proposals

**Testable (run the loop):**
- Hook logic changes (new conditions, different markers, adjusted thresholds)
- Module content changes (new checklist items, revised guidance)
- Skill amendments (threshold changes, new dispatch rules)
- Dispatch pattern changes (file-level scoping adjustments, branch strategy)
- Completion checklist changes (new evidence requirements, format changes)

**Not testable (present proposal directly):**
- New memory categories (structural, no behavioral change to test)
- Documentation-only updates
- New module creation (no baseline to compare against)
- Tooling additions (e.g., adding a new MCP server -- requires installation)

## The experiment loop

### 1. Setup
- Select the test task from ~/.claude/evolution/tasks/ that best exercises the proposal being tested. Consult the selecting metrics table in metrics.md to choose the right primary and secondary metrics.
- If no existing task fits, create a targeted task for this proposal in the tasks/ directory.
- Record the current baseline for those metrics (from baseline.json or from the most recent comparable run).

### 2. Branch
```bash
git checkout -b evolution/<proposal-tag>
```

### 3. Apply
- Implement the proposed change on the evolution branch.
- Changes are limited to workflow system files (skills, hooks, modules, CLAUDE.md). No application code changes.

### 4. Test -- Hybrid execution

**Module/checklist changes:** Dispatch a subagent with the modified content injected directly into its prompt. The subagent runs the test task. This tests whether the module change affects agent behavior without requiring a fresh session.

**Hook/skill changes (cross-session handoff):**
1. Save experiment state to hermes-bridge:
   ```
   checkpoint_save(
     summary="evolution-experiment-pending",
     key_decisions=[
       "proposal: <proposal-tag>",
       "test_task: <task-name>",
       "metrics: <comma-separated list>",
       "branch: evolution/<proposal-tag>",
       "baseline: <relevant baseline values from baseline.json>"
     ]
   )
   ```
2. Commit modified workflow files on the evolution branch.
3. Tell the user:
   > "Experiment `<tag>` is ready to test but requires a fresh session (the change affects hooks/skills loaded at startup). Please start a new session on the `evolution/<tag>` branch and run: 'Read ~/.claude/evolution/run-evolution.md and resume experiment <tag> using checkpoint_restore()'"
4. New session: restores checkpoint, reads this protocol, identifies the test task and metrics, runs the test task, collects automated metrics.
5. After completion: automated metrics are appended to evolution-log.md on the evolution branch. Human-evaluated metrics are flagged for review.
6. User returns to review results. The evolution log entry and the branch diff provide all context needed.

### 4.5. Collect Automated Metrics from Transcript

After the test task completes:

1. Identify the session transcript:
   `~/.claude/projects/{PROJECT}/{SESSION_ID}.jsonl`
   The session ID is available from the conversation context.

2. Parse for context_tokens:
   Sum all `message.usage` fields across entries:
   - `input_tokens`
   - `output_tokens`
   - `cache_read_input_tokens`
   - `cache_creation_input_tokens`

3. Parse for tool_calls:
   Count assistant entries containing `tool_use` content blocks.

4. Parse for time_to_completion:
   First timestamp minus last timestamp in the transcript.

5. If better-ccflare proxy is running, query for session_cost:
   `curl http://localhost:8080/api/requests?since=<experiment_start_timestamp>`
   Sum `cost_usd` across returned requests.

6. For subagent transcripts (team-dispatch experiments):
   Include token totals from `.../{SESSION_ID}/subagents/agent-{AGENT_ID}.jsonl`.
   Sum across all transcripts for the full experiment token count.

7. Record all automated metrics in the experiment report.

This parsing is done inline by the agent executing the experiment (no helper script). The agent uses grep/jq or direct file reading on the JSONL.

### 5. Evaluate
- Compare automated metrics against baseline.
- Prepare a report containing:
  - The proposal (what was changed and why)
  - The diff (exact files modified)
  - The test task used
  - Metric results vs. baseline (table format)
  - Any qualitative observations from the test run

### 6. Decide
- **Clear improvement** (primary metric better, no secondary metric significantly worse): Present to user with recommendation to accept. Keep the branch.
- **Mixed results** (some metrics better, some worse): Present to user with tradeoff analysis. Keep the branch for user decision.
- **Clear regression** (primary metric worse): Record in evolution-log.md with full data. Add to declined-proposals.md with the reason and data. Do not delete the branch.
- **Inconclusive** (metrics within noise margin): Note as inconclusive. May warrant a second test with a different task.

### 7. Record
All experiments are logged in ~/.claude/evolution/evolution-log.md:

```
## Experiment: <proposal-tag>
Date: <date>
Proposal: <one-line summary>
Test task: <task name>
Branch: evolution/<proposal-tag>
Status: accepted | declined | inconclusive | pending-user-review

### Metrics
| Metric              | Baseline | Result  | Delta  |
|---------------------|----------|---------|--------|
| <metric>            | <value>  | <value> | <+/-%> |

### Decision
<accepted/declined/inconclusive -- with reasoning>

### User notes (filled in after review)
<user's assessment, if any>
```
