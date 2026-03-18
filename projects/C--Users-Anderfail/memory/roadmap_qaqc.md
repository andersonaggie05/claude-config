---
name: roadmap_qaqc
description: QAQC V2 Overhaul status — Releases 1-3 done, Release 4 (Polish) next
type: project
---

QAQC V2 Overhaul — 4-release plan. Releases 1-3 complete.

- **Release 1** (Flag Overhaul & Metrics Split) — MERGED. PR #14. Severity changes, Unspecified Repair Technician flag, metrics split (pass_rate/alert_rate).
- **Release 2** (Dashboard UX) — MERGED. PR #15. Sortable tables, collapsible sections, drill-down, tooltips, severity contrast. 424 tests.
- **Release 3** (Repair Scorecard Restructuring) — PR #16 open. Summary tab, Company Performance tab, 3-category technician groupings, repair tooltips. 432 tests.
- **Release 4** (Polish) — NOT STARTED. Two items: (1) Excel Flag Reference Tab Update with severity color fills and compliance/alert grouping across all 4 output workbooks, (2) End-User README as standalone HTML.

**Why:** Comprehensive update addressing flag severity accuracy, dashboard usability, repair scorecard restructuring, and end-user documentation.

**How to apply:** Release 4 is scoped to `validate.py` (write_validation_summary, write_flag_review), `scorecard.py` (write_scorecard_xlsx), `repair_scorecard.py` (write_repair_scorecard_xlsx), and a new HTML README file. Spec at `docs/superpowers/specs/2026-03-17-qaqc-v2-overhaul-design.md` lines 219-243. Use `_repair_leak()` and `_make_repair_exports()` helpers for repair tests (not `make_leak_detail`/`make_exports`).
