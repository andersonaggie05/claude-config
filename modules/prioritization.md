---
name: Prioritization
description: RICE-based sprint prioritization methodology for ranking competing work items and assembling sprint plans
type: knowledge-module
source: C:/Users/Anderfail/.claude/agents/sprint-prioritizer.md
---

# Prioritization

Maximize business value per unit of effort. Cut scope before missing deadlines. A shipped 80% solution beats a perfect plan that never executes.

## Scope

Score and prioritize backlog items, assess capacity, identify dependencies, and assemble sprint plans. Do NOT perform architecture design, code review, or implementation — those are separate concerns.

## RICE Scoring

Score every candidate item before placing it in a sprint.

| Factor | Description | Scale |
|--------|-------------|-------|
| **Reach** | Users or workflows affected per sprint | Count or estimate |
| **Impact** | Contribution to project goals | 0.25 (minimal) / 0.5 / 1 / 2 / 3 (massive) |
| **Confidence** | Certainty in the estimates | 50% (low) / 80% (medium) / 100% (high) |
| **Effort** | Person-sprints required | Relative sizing |

**Score = (Reach × Impact × Confidence) / Effort**

Higher score = higher priority. When scores are close, prefer the item that unblocks more downstream work.

## Prioritization Process

### 1. Inventory

Collect all candidate items from:
- Project roadmaps (next planned milestones)
- New requirements or bug reports
- Tech debt items flagged in retrospectives
- Compliance gaps identified by auditors

### 2. Score Each Item

Apply RICE to every candidate. Document assumptions explicitly — a 100% confidence score requires strong justification.

### 3. Dependency Analysis

Before finalizing order:
- Map cross-project dependencies (e.g., a QAQC change that blocks an Appendix K feature)
- Identify items that unblock multiple downstream tasks — these get a priority bump
- Flag external dependencies (API changes, infra requirements, third-party timelines)

### 4. Sprint Plan Assembly

Rules for building the committed list:
- Match top-scored items to available capacity
- Reserve 15% buffer for uncertainty and interrupts — do not commit this capacity
- Group related items to minimize context switching
- Include at least one tech debt or compliance item per sprint

## Output Format

```
## Sprint Plan: [Sprint Name / Date Range]

### Sprint Goal
[One sentence describing the primary objective]

### Committed Items (ordered by priority)

| # | Item | Project | RICE Score | Effort | Dependencies |
|---|------|---------|------------|--------|-------------|
| 1 | [Description] | [Project] | [Score] | [Size] | [Blockers] |

### Capacity
- Available: [X] person-sprints
- Committed: [Y] person-sprints
- Buffer: [Z] person-sprints (15%)

### Deferred (scored but not fitting this sprint)
| Item | RICE Score | Reason Deferred |
|------|------------|-----------------|
| [Description] | [Score] | Capacity / dependency / strategic |

### Risks
1. [Risk description] — Mitigation: [Action]

### Cross-Project Dependencies
- [Dependency description and resolution plan]
```

## Connections
- Depends on: [[completion-checklist]]
- Related skills: [[architecture]] (top-priority items feed into architecture design), [[compliance-audit]] (compliance gaps feed into prioritization input), [[agent-pipelines]] (sprint-prioritizer is the optional planning stage before feature implementation)
- Tags: #prioritization #planning
