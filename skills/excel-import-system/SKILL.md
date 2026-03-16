---
name: excel-import-system
description: Use when adding new import types, modifying the Excel parser, working with import validation, column mapping, value overrides, or the import task pipeline in apps/imports/
---

# Excel Import System

## Overview

Multi-step import pipeline: upload XLSX → auto-map columns → preview → validate → user confirms overrides → execute via Celery task. Uses openpyxl for parsing. Four import types with type-specific handlers. Performance audits are NOT bulk-created (signals required).

## Key Files

- `apps/imports/models.py` — `ImportJob` (TenantModel) with status lifecycle
- `apps/imports/parser.py` — `read_xlsx_rows()`, column auto-mapping, 4 validate functions
- `apps/imports/tasks.py` — `execute_import()` task + 4 handler functions
- `apps/imports/views.py` — upload, preview, validate, column-mapping, value-overrides, execute endpoints
- `apps/imports/serializers.py` — API serializers
- `apps/imports/tests/` — test_parser.py, test_training_import.py, test_exports.py

## ImportJob Status Lifecycle

```
pending → validating → validation_complete → importing → completed | partial | failed
```

- `partial`: Some rows succeeded, some had errors (check `error_details`)
- `failed`: Entire import failed (exception during execution)

## Import Types

| Type | Handler | Bulk Create? | Post-Processing |
|------|---------|-------------|----------------|
| `surveys` | `_execute_survey_import` | Yes (batch 100) | Calls `_update_operator_hours()` per affected operator |
| `training_records` | `_execute_training_record_import` | Yes (batch 100) | Evaluates final tests, updates classroom date, calls `_recompute_qualification()` |
| `training_plans` | `_execute_training_plan_import` | Yes (all at once) | None |
| `performance_audits` | `_execute_performance_audit_import` | **No** — one at a time | Triggers `on_audit_save` signal per record |

**Critical:** Performance audits use `objects.create()` individually because the `on_audit_save` signal must fire for each record to correctly compute consecutive failures and trigger suspension. Records are sorted by `audit_date` ascending for correct ordering.

## Column Auto-Mapping

`parser.py` defines expected column names for each import type with synonyms:

```python
SURVEY_COLUMNS = {
    'survey_date': ['survey_date', 'date', 'survey date'],
    'facility': ['facility_id', 'facility_name', 'facility', 'site'],
    'operator': ['operator_name', 'operator_id', 'operator', 'surveyor'],
    ...
}
```

Headers from the uploaded XLSX are matched case-insensitively against these synonyms. Users can override via the column-mapping API endpoint.

## Value Overrides

After validation, unrecognized regulation text or facility types are surfaced. Users confirm canonical mappings via `value_overrides` JSON field:

```json
{
  "regulation_overrides": {"NSPS OOOO-a": "NSPS OOOOa"},
  "facility_type_overrides": {"Gas Plant": "Natural Gas Processing Facility"}
}
```

Applied during execution before `detect_appendix_k()` is called.

## Adding a New Import Type

### Step 1: Add to `IMPORT_TYPE_CHOICES` in `apps/imports/models.py`

```python
('my_new_type', 'My New Type'),
```

### Step 2: Add column mapping in `apps/imports/parser.py`

```python
MY_NEW_TYPE_COLUMNS = {
    'field_name': ['field_name', 'field name', 'alias1', 'alias2'],
    ...
}
```

### Step 3: Add validation function in `apps/imports/parser.py`

Follow existing `validate_*_rows()` pattern. **Return signature:** `(valid_rows, errors, info, stats)` — all 4 values required. Errors use `{'row': idx + 2, 'error': str(e)}` format (row 2 = first data row after header).

### Step 4: Add handler in `apps/imports/tasks.py`

Follow existing `_execute_*_import()` pattern. Call `read_xlsx_rows()`, validate, `_apply_validation_stats()`, then bulk/individual create.

### Step 5: Wire handler into `execute_import()` dispatcher

Add entry to the handler dict in `execute_import()`.

### Step 6: Decide bulk vs individual create

- **Use `bulk_create`** if the model has no post_save signal side effects (or you'll call handler functions manually afterward)
- **Use `objects.create()` individually** if post_save signals must fire per record (like performance audits)

If using bulk_create, you MUST manually call any signal handler functions that would normally fire on save (e.g., `_update_operator_hours()`, `_recompute_qualification()`).

## Common Mistakes

- **Using `bulk_create` for performance audits** — bypasses `on_audit_save` signal, consecutive failure tracking breaks. This fails **silently** — audits are created but suspension never triggers. There is no guard rail; only the developer knows which models need signals
- **Not sorting audit imports by date** — out-of-order creates produce wrong consecutive failure counts
- **Forgetting `_apply_validation_stats()`** — error/info/stats not stored on the job
- **Missing the 4-value return signature** from validate functions — `(valid_rows, errors, info, stats)`
- **Not calling signal handlers after bulk_create** — operator hours and qualification status won't update
- **Using `create()` instead of `bulk_create` for surveys/training** — unnecessarily slow for large imports
- **Forgetting `transaction.atomic()`** — all existing handlers run inside the parent task's `transaction.atomic()` block. If you extract a handler to run standalone, wrap it in `transaction.atomic()` yourself or partial failures leave inconsistent data
- **Modifying handler without understanding the atomic scope** — removing or nesting `transaction.atomic()` changes rollback behavior for the entire import


## Amendments
