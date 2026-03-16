---
name: vault-standup
description: Cross-project briefing from roadmaps, recent sessions, and Kanban boards
---

# /vault-standup

Scan project state and deliver a briefing.

## Process

1. Read all roadmap memory files (roadmap_appendix_k.md, roadmap_qaqc.md)
2. Search recent sessions via `session_search("recent work")` for last 3 sessions
3. Read Kanban boards (appendix-k-board.md, qaqc-board.md, system-health-board.md)
4. Summarize: what's done, what's in progress, what's blocked, what's next

## Output Format

```
STANDUP — {date}
================
## Appendix K
- Status: {current sub-project and state}
- Recent: {last session's work}
- Next: {next planned work}
- Blockers: {any}

## QAQC Framework
- Status: {current work and state}
- Recent: {last session's work}
- Next: {next planned work}
- Blockers: {any}

## System Health
- Pending improvements: {count from system-health-board}
- Hook violations last 5 sessions: {count if trackable}
```
