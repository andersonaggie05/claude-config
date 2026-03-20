---
name: feedback_plan_vs_intent
description: Plans must be validated against the user's original intent, not just executed literally — if a plan doesn't solve the stated problem, flag it
type: feedback
---

When executing a plan, validate each step against the user's original stated problem — not just the plan's literal instructions.

**Why:** During QAQC V3, the user's original request included "add filters by region" and "change the default display so not everything is displayed at once" for the Summary tab. The plan only specified a scope toggle (CQ/All Time) and pagination — neither of which solved the core problem (3,930 records rendering at once). The plan was executed literally without flagging that it didn't address the user's stated requirements. The user had to call this out explicitly.

**How to apply:** Before implementing a plan section, ask: "Does this step actually solve the problem described in the Context section?" If the plan says "add toggle" but the problem is "tab freezes the browser with 43k DOM nodes," the toggle doesn't solve the problem — flag it and propose the right fix (filter-first pattern, lazy rendering, etc.).
