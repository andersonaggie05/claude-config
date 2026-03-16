---
name: Thoroughness Over Speed
description: Never optimize for speed — always optimize for thoroughness. Absolute requirement that must never be violated.
type: feedback
---

Never optimize for speed, always optimize for thoroughness. This is an absolute requirement and must never be violated.

**Why:** User is building compliance architecture (EPA regulations) where mistakes cannot be allowed. Claude was caught ignoring the plan review loop, marking tasks complete when they weren't done, skipping Prettier, and not going through task lists. These failures compounded because advisory-only rules were being skipped under context pressure.

**How to apply:** Every workflow step must be followed mechanically. Never skip a checklist item to save time. Never mark a task complete without running the completion checklist. Never exit plan mode without the review loop. If unsure whether to be thorough or fast, always choose thorough. Hard enforcement hooks now exist to catch violations — if a hook fires, it means the upstream process failed and the retrospective must capture why.

## Connections
- Related: [[workflow-protocol]], [[completion-checklist]]
- Tags: #feedback #enforcement
