---
name: roadmap_qaqc
description: QAQC V3 Revision COMPLETE + Summary tab fix — PRs #18 and #19 merged, 457 tests, 88% coverage
type: project
---

QAQC V2 Overhaul — ALL COMPLETE as of 2026-03-18 (PRs #14-17).

QAQC V3 Revision — ALL COMPLETE as of 2026-03-19. PR #18 + PR #19.

- **PR #18** (V3 Revision) — MERGED. Coverage infra, compliance_rate/flag_rate rename, quarterly scoping, lazy tabs, CLI timing. 451 tests.
- **PR #19** (Summary Tab Fix) — MERGED. Filter-first redesign: region pills, searchable facility selector, sortable tables via makeSortableTable. Default shows nothing until user selects regions/facilities. 457 tests.

Portable bundle rebuilt: `build/OGI_Validation.zip` (16.4 MB).

**How to apply:** V3 is done. Summary tab uses filter-first pattern — study `renderSummary()` before modifying. Use `_repair_leak()` and `_make_repair_exports()` for repair tests. `parse_date()` cannot parse `str(datetime)` — carry raw datetime objects via `_due_dt` pattern.
