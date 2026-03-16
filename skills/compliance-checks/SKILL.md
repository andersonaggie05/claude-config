---
name: compliance-checks
description: Use when modifying compliance check logic, alert types, thresholds, the nightly Celery task, or adding new compliance checks to the Appendix K system
---

# Compliance Checks

## Overview

Six compliance check functions run nightly via Celery (producing 7 alert types — `check_survey_gap` covers both 12mo and 24mo), evaluating each non-inactive operator against EPA Appendix K thresholds. Checks create/update/resolve `ComplianceAlert` records using an idempotent pattern. A `ComplianceSnapshot` is created daily after all checks complete.

## Key Files

- `apps/compliance/checks.py` — all 6 check functions + `run_all_checks()` + `create_snapshot()`
- `apps/compliance/models.py` — `ComplianceAlert` (7 alert types, 4 severities), `ComplianceSnapshot`, `WeeklyAlertSummary`
- `apps/compliance/tasks.py` — `run_nightly_compliance_checks` (2:00 AM daily), `generate_weekly_alert_summary` (Monday 6:00 AM)
- `apps/compliance/tests/test_checks.py` — test patterns

## EPA-Mandated Thresholds

**Do not change these without regulatory justification.**

| Constant | Value | Meaning |
|----------|-------|---------|
| `SENIOR_HOURS_THRESHOLD` | 40 | Rolling 12-month survey hours for senior status |
| `SENIOR_CAREER_HOURS` | 1400 | Career total hours for senior eligibility |
| `BIENNIAL_YEARS` | 2 | Classroom refresher training cycle |
| `BIENNIAL_WARNING_DAYS` | 90 | Alert this many days before refresher due |
| `AUDIT_INTERVAL_MONTHS` | 6 | Semiannual performance audit cycle |
| `AUDIT_WARNING_DAYS` | 30 | Alert this many days before audit due |
| `CONSECUTIVE_FAILURE_LIMIT` | 2 | Failures triggering suspension + retraining |
| `RECORD_RETENTION_YEARS` | 5 | Record retention requirement |
| `RECORD_RETENTION_WARNING_DAYS` | 90 | Alert before retention expiry |

## Alert Types and Severities

| Alert Type | Warning Trigger | Critical/Overdue Trigger |
|------------|----------------|--------------------------|
| `biennial_refresher_due` | 90 days before due | Overdue |
| `semiannual_audit_due` | 30 days before due | Overdue |
| `consecutive_audit_failures` | — | >=2 consecutive failures |
| `survey_gap_12mo` | — | >12 months since last survey (unless 40h exemption) |
| `survey_gap_24mo` | — | >24 months since last survey |
| `senior_hours_at_risk` | Rolling 12mo < 40h for senior | — |
| `record_approaching_expiry` | 90 days before 5-year mark (info severity) | — |

Severities: `info`, `warning`, `critical`, `overdue`

## The 40-Hour Exemption

Operators with >= 40 rolling 12-month survey hours are exempt from 12-month survey gap retraining. Check `check_survey_gap()` in `checks.py` lines 170-172.

## Idempotent Alert Pattern

```python
# Create or update (does NOT create duplicates)
_create_or_update_alert(operator, alert_type, severity, title, message, due_date=None)

# Auto-resolve when condition clears
_resolve_alert(operator, alert_type)
```

`_create_or_update_alert` checks for existing unresolved alert of same type for same operator. If found, updates severity/title/message. If not found, creates new. This makes checks safe to run multiple times.

`_resolve_alert` marks all unresolved alerts of that type as resolved with timestamp.

**Every check function must call `_resolve_alert` in the else branch** — when the condition is no longer met, the alert must auto-close.

## Adding a New Compliance Check

### Step 1: Choose an alert type slug that fits in `max_length=30`

The `alert_type` field is `CharField(max_length=30)`. Count your characters. If over 30, use a shorter name or you'll need an `AlterField` migration.

### Step 2: Add to `ALERT_TYPE_CHOICES` in `apps/compliance/models.py`

```python
('training_activity_gap', 'Training Activity Gap'),
```

### Step 3: Write the check function in `apps/compliance/checks.py`

Follow this pattern:

```python
def check_training_activity_gap(operator):
    """Alert when no training activity in 90 days."""
    # Query from already-prefetched data (run_all_checks uses prefetch_related)
    last_record = (
        operator.training_records
        .filter(status='completed')
        .order_by('-end_date', '-start_date')
        .first()
    )
    if not last_record:
        return  # New operators with no records — don't alert
    last_date = last_record.end_date or last_record.start_date
    days_since = (timezone.now().date() - last_date).days

    if days_since >= 90:
        _create_or_update_alert(...)
    elif days_since >= 75:
        _create_or_update_alert(...)  # warning severity
    else:
        _resolve_alert(operator, 'training_activity_gap')
```

**Key design decisions:**
- Query `TrainingRecord` directly rather than adding a cached field. A cached field requires a model migration, signal changes, backfill migration, and serializer updates — disproportionate for a nightly-only consumer. Note: `.filter()` on a prefetched relation issues a new DB query (Django ignores the prefetch cache when you chain `.filter()`). This is fine for a nightly batch job — one small indexed query per operator is negligible.
- Handle "no records" gracefully — `return` without alerting to avoid false-positive storm for new operators.
- Consider whether `in_training` operators should be included (they likely should — stalled trainees are important to flag). The codebase is inconsistent: `check_semiannual_audit` excludes `in_training`, other checks do not.
- **`due_date` convention:** Pass `due_date` when the alert is about an upcoming deadline (biennial refresher, semiannual audit). Omit it for gap-based conditions where the alert describes something that has already elapsed.
- **Threshold boundaries:** Use `>=` (inclusive) for day thresholds to match existing patterns (`days_until <= BIENNIAL_WARNING_DAYS`).

### Step 4: Wire into `run_all_checks()` in `checks.py`

Add one line inside the operator loop:

```python
check_training_activity_gap(operator)
```

That's it. The Celery task and beat schedule need no changes — they call `run_all_checks()`.

### Step 5: Do NOT add a new `ComplianceSnapshot` field

The existing `open_critical_alerts` and `open_warning_alerts` already count alerts by severity across all types. A per-type counter adds migration + code complexity for no reporting benefit.

### Step 6: Write tests in `apps/compliance/tests/test_checks.py`

Test: alert created at threshold, warning at pre-threshold, resolved when condition clears, no alert for new operators, idempotency (run twice = same result).

### Step 7: Create the migration

```bash
python manage.py makemigrations compliance
```

This creates the `AlterField` for `ALERT_TYPE_CHOICES`. No data migration needed unless you added a cached field (which you shouldn't).

## Common Mistakes

- Alert type slug exceeding `max_length=30` — always count characters
- Adding a cached `DateField` on Operator when a query suffices — over-engineering that requires model change, signal, backfill migration, and serializer updates
- Forgetting the backfill migration if you DO add a cached field — causes false-positive alert storm on first nightly run (every existing operator gets CRITICAL)
- Missing the `_resolve_alert()` else branch — alerts never auto-close
- Not handling new operators (zero records) — immediate false CRITICAL for every new hire
- Adding to `ComplianceSnapshot` unnecessarily — severity-based counters already capture the data
- Forgetting that `run_all_checks()` already uses `prefetch_related('training_records', 'performance_audits')` — the data is already loaded, no extra queries needed


## Amendments
