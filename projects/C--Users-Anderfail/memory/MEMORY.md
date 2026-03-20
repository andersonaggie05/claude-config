# Memory Index

## User
- [[user_remote_setup]] — Remote VS Code setup + useful Claude Code features (/remote-control, /btw, /loop, /rewind)

## Projects
- [[project_mobile_initiative]] — Appendix K mobile/tablet PWA initiative with 4 sub-projects
- [[project_self_improving_agents]] — Self-improving agent ecosystem: workflow-protocol skill, knowledge modules, hard enforcement hooks, automatic retrospective, Obsidian vault

## Feedback
- [[feedback_thoroughness]] — Never optimize for speed, always thoroughness. Absolute requirement.
- [[feedback_no_lower_thresholds]] — Never lower test coverage thresholds; write tests instead
- [[feedback_venv_tooling]] — Ruff/pytest may not be in appendix_k venv; use .venv/Scripts/ path directly
- [[feedback_ci_trigger_scope]] — CI only triggers on push to main or PRs targeting main, not feature branches
- [[feedback_test_integrity]] — Never modify a test to force it to pass; fix the site if a test reveals a real bug
- [[feedback_parse_date_format]] — parse_date() can't parse str(datetime); carry raw datetime objects instead of re-parsing
- [[feedback_plan_accuracy]] — Plans must read actual model/schema files before writing code snippets
- [[feedback_lint_baseline]] — Run full lint as first commit on feature branches to separate formatting from feature work
- [[feedback_plan_diagnosis]] — Plan diagnosis steps should frame root causes as hypotheses, not assertions
- [[feedback_subagent_test_context]] — When dispatching subagents to modify files, include tests that assert invariants about those files
- [[feedback_plan_vs_intent]] — Plans must be validated against user's original intent, not just executed literally
- [[feedback_subagent_imports]] — Include correct import paths when dispatching subagents (e.g. apps.accounts.models for User)
- [[feedback_component_boundaries]] — OperatorDetailPage has nested function components needing props threaded through

## Navigation
- [[navigation_appendix_k]] — Key file locations in Appendix K (signals, compliance, imports, frontend components)
- [[navigation_qaqc]] — Key file locations in QAQC Framework (validate.py, scorecard modules, CLI)

## Roadmap
- [[roadmap_appendix_k]] — Appendix K status: Phases 1-2 done, Phase 3 (PWA infra) spec approved, Phases 4-5 planned
- [[roadmap_qaqc]] — QAQC V3 Revision COMPLETE — PRs #18 + #19 merged, 457 tests, 88% coverage

## Decision Journals
- Appendix K: `appendix_k/docs/decisions/DECISIONS.md` (16 architectural decisions)
- QAQC Framework: `QAQC Framework/docs/decisions/DECISIONS.md` (14 architectural decisions)

## References
