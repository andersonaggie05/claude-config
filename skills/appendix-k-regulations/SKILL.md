---
name: appendix-k-regulations
description: Use when working with Appendix K detection logic, EPA regulation patterns, facility type mappings, RegulationFacilityMapping, or adding new regulations to the survey system
---

# Appendix K Regulations

## Overview

Determines whether a survey qualifies as Appendix K based on regulation + facility type combination. Regex patterns match regulations; `RegulationFacilityMapping` stores eligibility with 1-hour cache.

## Key Files

- `apps/surveys/appendix_k.py` — `REGULATION_PATTERNS`, detection, fuzzy matching
- `apps/surveys/models.py` — `RegulationFacilityMapping` (global, no company FK), `Survey.save()` auto-detection
- `apps/surveys/admin.py` — `list_editable` on `is_appendix_k` triggers save → invalidation → recompute
- `apps/facilities/models.py` — 14 facility types, `effective_facility_type`
- `apps/surveys/migrations/0009*.py` — canonical data migration pattern

## Regulation Truth Table

| Regulation | CFR | Appendix K Facility Types | Non-Appendix K Types |
|------------|-----|--------------------------|---------------------|
| NSPS XXa | 40 CFR 60.500 | Gasoline Loading Rack, Bulk Gasoline Terminal | — |
| NSPS OOOOa | 40 CFR 60.5360a | — (NONE qualify) | Well Site, Compressor Station, NGPF, CPF |
| NSPS OOOOb | 40 CFR 60.5360b | NGPF ONLY | Well Site, Compressor Station, CPF |
| NSPS OOOOc | 40 CFR 60.5360c | NGPF ONLY | Well Site, Compressor Station, CPF |
| MACT BBBBBB | 40 CFR 63 BBBBBB | Bulk Gas Terminal, Pipeline Breakout/Pumping Stn, Bulk Gas Plant | — |
| MACT R | 40 CFR 63 R | Bulk Gasoline Terminal, Pipeline Breakout Station | — |

**Critical:** OOOOa is NEVER Appendix K. OOOOb/OOOOc are Appendix K ONLY for NGPF.

Mapping rows: 2+4+4+4+4+2 = 20 (`test_mapping_seeded` asserts this — increment when adding).

## Architecture

- **`REGULATION_PATTERNS`** — compiled regex dict keyed by canonical code (space-separated: `'NSPS OOOOb'`, `'MACT R'`)
- **`RegulationFacilityMapping`** — `unique_together = [('regulation_code', 'facility_type')]`. Both fields use title-case display strings (e.g., `'Natural Gas Processing Facility'`)
- **Cache** — `_get_mapping()` caches 1hr. `save()`/`delete()` → `invalidate_mapping_cache()` → `recompute_appendix_k_flags.delay()`
- **`Survey.save()`** → `detect_appendix_k()` using `facility.effective_facility_type` (`regulatory_facility_type or facility_type`)

## Adding a New Regulation

### Step 1: Add regex to `REGULATION_PATTERNS`

Cover three alternations: `NSPS <code>`, `subpart <code>`, `40 CFR <section>`.

**Regex rules:**
- `(?!\w)` lookahead on short codes prevents matching longer codes (OOOOa→OOOOb). See OOOOa pattern.
- **Known gap:** OOOOb/OOOOc bare forms lack `(?!\w)` — safe because no OOOOba/ca exist. New OOOO-variants MUST add it.
- Bare short codes need prefix ("BBBBBB" safe; "Kb" not — conflicts with kilobytes).
- Cover full CFR section range (`60.11[0-7]b` for multi-section subparts).

### Step 2: Data migration

Follow `0009*.py` pattern:
- `get_or_create` not `create` — `unique_together` constraint fails on re-runs
- Include `reverse` function deleting added rows
- `apps.get_model()` bypasses custom `save()` — no cache invalidation or recompute from migrations

### Step 3: Exhaustive tests

Test EVERY facility type (positive AND negative) through all detection functions: `normalize_regulation()`, `find_regulations_in_text()`, `find_unrecognized_regulations()`. Cross-regulation smoke test existing results.

### Step 4: Recompute existing surveys

Run `recompute_appendix_k_flags.delay()` after deploying (NOT the management command — it uses `.facility_type` instead of `.effective_facility_type`).

## Common Mistakes

- `.facility_type` instead of `.effective_facility_type` — ignores regulatory override
- Missing negative test cases — every non-qualifying facility type must be tested
- `create()` instead of `get_or_create()` in migrations — breaks on `unique_together`
- Missing reverse migration function
- Bare short codes in regex without prefix — false positive risk


## Amendments
