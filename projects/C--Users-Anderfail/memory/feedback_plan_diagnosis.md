---
name: feedback_plan_diagnosis
description: Plan diagnosis steps should frame root causes as hypotheses, not assertions — investigate, don't assume
type: feedback
---

When a plan includes a diagnosis/debugging section, root cause hypotheses should be framed as things to investigate, not stated as fact.

**Why:** During QAQC V3, the plan said "The number is ~1099 (= D.total)" as an assertion. The actual bug was CSS `\\2195` rendering literally — completely different root cause. The plan's diagnosis methodology (use Playwright, take screenshot) was correct, but the asserted cause wasted investigation time.

**How to apply:** In plan diagnosis sections, write "Investigate what the number is and where it comes from" not "The number is ~1099." Frame fix sections as "Once root cause is identified, fix accordingly" not "Fix the template literal that leaks the count."
