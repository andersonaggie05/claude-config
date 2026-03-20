---
name: feedback_plan_accuracy
description: Plans must read actual model/schema files before writing code snippets — plan approximations cause implementer rework
type: feedback
---

Implementation plans must include actual model field definitions, not approximations from memory or specs. During Phase 3 PWA, the plan incorrectly assumed facility FKs on TrainingRecord/PerformanceAudit, used `phase` instead of `training_phase`, and missed that Company requires `slug`. Every implementer had to adapt.

**Why:** Plan code snippets are treated as authoritative by subagent implementers. When they're wrong, every task starts with debugging model field mismatches instead of building the feature. This wastes time and introduces risk.

**How to apply:**
- During planning (writing-plans skill), read actual model files before writing test fixtures or view code
- When dispatching implementers, include the actual model class definition in the prompt context
- For backend tasks, always include the relevant model's fields, required args, and FK relationships

## Connections
- Related: [[feedback_thoroughness]]
- Tags: #feedback #planning #workflow
