---
name: roadmap_qaqc
description: QAQC V2 Overhaul COMPLETE — all 4 releases merged, 439 tests, portable bundle rebuilt
type: project
---

QAQC V2 Overhaul — 4-release plan. ALL COMPLETE as of 2026-03-18.

- **Release 1** (Flag Overhaul & Metrics Split) — MERGED. PR #14. Severity changes, Unspecified Repair Technician flag, metrics split (pass_rate/alert_rate). 424 tests.
- **Release 2** (Dashboard UX) — MERGED. PR #15. Sortable tables, collapsible sections, drill-down navigation, tooltips, severity contrast fix. 424 tests.
- **Release 3** (Repair Scorecard Restructuring) — MERGED. PR #16. Summary tab, Company Performance tab, 3-category technician groupings, repair-specific tooltips. 432 tests.
- **Release 4** (Polish) — MERGED. PR #17. Severity-colored Flag Legend in all 4 Excel outputs via shared `write_flag_legend_sheet()`, end-user README.html. 439 tests.

Portable bundle rebuilt: `build/OGI_Validation.zip` (16.4 MB).

**Design spec:** `docs/superpowers/specs/2026-03-17-qaqc-v2-overhaul-design.md`

**How to apply:** V2 overhaul is done. Next work is field-feedback-driven improvements or new check types. Use `_repair_leak()` and `_make_repair_exports()` helpers for repair tests (not `make_leak_detail`/`make_exports`).
