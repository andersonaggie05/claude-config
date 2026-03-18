# Evolution Metric Suite

Each evolution experiment selects the metric(s) relevant to the proposal being tested.

## Automated (collected during experiment)

| Metric             | Source                  | How to collect                                                                                                                                                                                              |
|--------------------|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| hook_block_count   | session transcript      | Count hook-injected block messages in conversation                                                                                                                                                          |
| test_pass_rate     | test runner output      | From redirected log: passed_first_try or N fix_cycles                                                                                                                                                       |
| scope_adherence    | git diff + checkpoint   | Compare files in diff vs assigned file list from checkpoint                                                                                                                                                 |
| time_to_completion | wall clock              | Start: first agent action. End: checklist sign-off                                                                                                                                                          |
| context_tokens     | JSONL transcript        | Parse `~/.claude/projects/{PROJECT}/{SESSION}.jsonl`, sum `message.usage.input_tokens + output_tokens + cache_read_input_tokens + cache_creation_input_tokens` across all entries. Cross-validate with better-ccflare DB if proxy is running. |
| tool_calls         | JSONL transcript        | Count entries in transcript where assistant message contains `tool_use` content blocks                                                                                                                      |
| session_cost       | better-ccflare DB       | Query `SELECT SUM(cost_usd) FROM requests WHERE timestamp >= <experiment_start>`. Only available when proxy is running; nullable otherwise.                                                                 |

## Human-Evaluated (assessed after experiment)

| Metric               | What to assess                                    |
|----------------------|---------------------------------------------------|
| discovery_efficiency | How many file reads before productive work started |
| plan_quality         | Was plan complete, realistic, no phantom items? [1-5] |
| rework_needed        | Did human correct agent work? [none/minor/significant] |
| output_usefulness    | For non-code tasks, usable as-is? [1-5]           |
| retrospective_quality| Did Layer 3 produce actionable proposals? [1-5]   |

## Selecting Metrics

| Proposal type              | Primary metric       | Secondary metrics                              |
|----------------------------|----------------------|------------------------------------------------|
| Hook change                | hook_block_count     | test_pass_rate, scope_adherence                |
| Module update              | plan_quality         | tool_calls, rework_needed                      |
| Dispatch pattern change    | discovery_efficiency | scope_adherence, tool_calls                    |
| Completion checklist change| test_pass_rate       | context_tokens, hook_block_count               |
| workflow-protocol change   | time_to_completion   | context_tokens, tool_calls, all other automated|
