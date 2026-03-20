---
name: feedback_component_boundaries
description: OperatorDetailPage has nested function components that need props threaded — check component boundaries before adding state references
type: feedback
---

When adding state variables to OperatorDetailPage, check whether the render locations are inside nested function components (TrainingPhaseAccordion, AuditsTable, ComplianceItem) that have their own prop interfaces. Variables defined in the main component are NOT in scope inside these nested components.

**Why:** Phase 4 added `offlineStatuses` to the main component but referenced it inside TrainingPhaseAccordion and AuditsTable without passing it as a prop. Required 3 tsc passes to fix.

**How to apply:** Before referencing a new variable in JSX, grep for `function.*{` declarations in the file to identify component boundaries. If the JSX is inside a nested component, add the variable to that component's props interface and pass it at all call sites.
