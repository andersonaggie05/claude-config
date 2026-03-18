---
name: Knowledge Modules
description: Composable expertise modules for context-scoped agent dispatch
type: index
---

# Knowledge Modules

Modules are composable units of expertise injected into agent prompts by the director during team dispatch. They are NOT loaded into the main conversation (except completion-checklist, which is embedded in workflow-protocol.md).

## Composition Mapping

| Task involves... | Include modules... | Also specify... |
|---|---|---|
| Any agent (always) | [[completion-checklist]] | Exact file list to modify |
| Backend implementation | [[verification]] | Exact file list to modify |
| Frontend implementation | [[verification]] | Exact file list to modify |
| Compliance feature | [[compliance-audit]] | Exact file list to modify |
| Architecture decision | [[architecture]] | Exact file list to modify |
| Security-sensitive change | [[security-review]] | Exact file list to modify |
| Multi-tenant change | [[security-review]] (tenant isolation section) | Exact file list to modify |
| Prioritization needed | [[prioritization]] | Exact file list to modify |

The "Also specify" column applies to every row. The file list comes from the director's plan analysis (see File-Level Scoping in workflow-protocol.md).

## Module Inventory

| Module | Source | Tags |
|--------|--------|------|
| [[verification]] | Reality Checker agent | #verification #quality-gate |
| [[architecture]] | Software Architect agent | #architecture #design |
| [[compliance-audit]] | Compliance Auditor agent | #compliance #epa #audit |
| [[security-review]] | Agent-pipelines | #security #multi-tenant |
| [[prioritization]] | Sprint Prioritizer agent | #prioritization #planning |
| [[completion-checklist]] | New (universal) | #enforcement #checklist |
