---
name: navigation_qaqc
description: Key file locations and code paths in the QAQC Framework validation engine
type: navigation
---

**Main engine:** `validate.py` (~2660 lines) — entry point, 23+ compliance checks (CHK1-CHK23+)
**CLI entry:** `cli_main(argv)` → `parse_args()` + `main()` — supports `--scorecard`, `--repair-scorecard`, `--clear-cache`, `--config-dir`, `--output-dir`

**Scorecard modules (sibling files):**
- `scorecard.py` (~800 lines) — contractor scorecard metrics + XLSX/HTML output
- `repair_scorecard.py` — repair analysis metrics + XLSX/HTML output
- `company_resolver.py` (~250 lines) — inspector-to-company mapping (exact → domain → unmatched)
- `cache_db.py` (~300 lines) — SQLite cache with row dedup, 180-day expiry
- `config_loader.py` — YAML config with hardcoded fallbacks

**Templates:** `templates/` — `dashboard_template.html`, `scorecard_template.html`, `repair_scorecard_template.html`
**Config files:** `validation_config/` — `company_config.yaml`, `technician_config.yaml`, `ogi_cache.db`
**Build:** `build_portable.py` — creates `build/OGI_Validation.zip` (embedded Python + openpyxl)

**Critical functions in validate.py:**
- `parse_date(val)` ~line 2300 — centralized date parsing (Excel serials + strings)
- `normalize_name(name)` — lowercase + strip + collapse whitespace
- `get_flag_severity(flag_name)` — maps flag prefix to red/orange/yellow
- `FLAG_SEVERITY` dict — centralized severity mapping for all flags
- `run_checks()` — orchestrates all 23+ checks

## Connections
- Related: [[run-tests]], [[verification]]
- Tags: #navigation #qaqc
