---
name: Knowledge Modules
description: Composable expertise modules for context-scoped agent dispatch
type: index
---

# Knowledge Modules

Modules are composable units of expertise injected into agent prompts by the director during team dispatch. They are NOT loaded into the main conversation (except completion-checklist, which is embedded in workflow-protocol.md).

## Composition Mapping

| Task involves... | Include modules... |
|---|---|
| Any agent (always) | [[completion-checklist]] |
| Backend implementation | [[verification]] |
| Frontend implementation | [[verification]] |
| Compliance feature | [[compliance-audit]] |
| Architecture decision | [[architecture]] |
| Security-sensitive change | [[security-review]] |
| Multi-tenant change | [[security-review]] (tenant isolation section) |
| Prioritization needed | [[prioritization]] |

## Module Inventory

| Module | Source | Tags |
|--------|--------|------|
| [[verification]] | Reality Checker agent | #verification #quality-gate |
| [[architecture]] | Software Architect agent | #architecture #design |
| [[compliance-audit]] | Compliance Auditor agent | #compliance #epa #audit |
| [[security-review]] | Agent-pipelines | #security #multi-tenant |
| [[prioritization]] | Sprint Prioritizer agent | #prioritization #planning |
| [[completion-checklist]] | New (universal) | #enforcement #checklist |
