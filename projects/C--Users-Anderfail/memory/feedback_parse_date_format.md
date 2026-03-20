---
name: feedback_parse_date_format
description: parse_date() cannot parse str(datetime) format like "2026-01-30 00:00:00" — carry raw datetime objects instead of re-parsing
type: feedback
---

When building derived data structures from dates already parsed by `parse_date()`, do NOT convert to string and re-parse. `parse_date()` handles Excel serials and specific date string formats but NOT `str(datetime)` output like `"2026-01-30 00:00:00"`.

**Why:** Discovered during V3 Release 3B — late repair entries stored `str(fa_due)` then tried to `parse_date(lr["due"])` for quarterly grouping. `parse_date` returned None, silently dropping all entries.

**How to apply:** When a downstream computation needs the raw datetime, carry it as an internal field (e.g., `_due_dt`) and strip it before JSON serialization. Use `_strip_internal()` or filter keys starting with `_`.
