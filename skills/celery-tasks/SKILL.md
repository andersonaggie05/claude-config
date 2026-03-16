---
name: celery-tasks
description: Use when adding Celery tasks, modifying the beat schedule, working with task timeouts or retries, or understanding how async tasks interact with signals and the import system
---

# Celery Tasks

## Overview

8 Celery tasks across 4 apps (compliance, surveys, notifications, imports) with Redis broker. Beat runs 5 periodic schedules. Global timeouts: 600s soft / 900s hard. Signals are synchronous (not tasks) — know the difference.

## Key Files

- `config/celery.py` — app config, global timeouts
- `config/settings/base.py` — `CELERY_BEAT_SCHEDULE` (5 entries: compliance, rolling hours, integrity, notifications, weekly summary)
- `config/settings/test.py` — `CELERY_TASK_ALWAYS_EAGER = True`
- `apps/compliance/tasks.py` — nightly checks, on-demand company check
- `apps/surveys/tasks.py` — rolling hours, integrity check, appendix_k recompute
- `apps/notifications/tasks.py` — scheduled emails, immediate alerts
- `apps/imports/tasks.py` — import execution with 4 type handlers

## Beat Schedule

All 5 entries are in `config/settings/base.py` (canonical location). **Always add new entries to `base.py` only.**

| Name | Task | Schedule |
|------|------|----------|
| `nightly-compliance-checks` | `...run_nightly_compliance_checks` | Daily 2:00 AM |
| `nightly-rolling-hours-update` | `...update_all_rolling_hours` | Daily 2:30 AM |
| `weekly-hour-cache-integrity` | `...verify_operator_hour_caches` | Sunday 3:00 AM |
| `send-notification-emails` | `...send_notification_emails` | Every 15min |
| `weekly-alert-summary` | `...generate_weekly_alert_summary` | Monday 6:00 AM |

## Task Inventory

| Task | App | Retries | Trigger | Key Detail |
|------|-----|---------|---------|------------|
| `run_nightly_compliance_checks` | compliance | None | Beat 2:00 AM | Per-company try/except, logs and continues |
| `run_company_compliance_check(company_id)` | compliance | None | API (POST) | On-demand single company |
| `generate_weekly_alert_summary` | compliance | None | Beat Mon 6:00 AM | Creates `WeeklyAlertSummary` per company for previous ISO week |
| `update_all_rolling_hours` | surveys | None | Beat 2:30 AM | Only saves if value changed |
| `verify_operator_hour_caches` | surveys | None | Beat Sun 3:00 AM | Checks all 5 cached fields, returns fix count |
| `recompute_appendix_k_flags` | surveys | None | Model save/delete | Triggered by `RegulationFacilityMapping.save()` |
| `send_notification_emails` | notifications | 3x, 60s | Beat every 15min | Per-company schedules, per-user preferences |
| `execute_import(import_job_id)` | imports | 3x, 60s | API | Routes to 4 type handlers |

## Timeouts and Retries

**Global (all tasks):**
```python
app.conf.task_soft_time_limit = 600   # 10 min → raises SoftTimeLimitExceeded
app.conf.task_time_limit = 900        # 15 min → hard kill
```

**Task-specific retries** (notification + import tasks only):
```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
```

Compliance and survey tasks have **no retry** — they use per-company try/except to continue on failure.

## Adding a New Beat Task

1. **Write task** in app's `tasks.py` using `@shared_task`. Pattern: iterate `Company.objects.filter(is_active=True)` with per-company try/except
2. **Add schedule** to `CELERY_BEAT_SCHEDULE` in `config/settings/base.py`. Do NOT add to `celery.py`
3. **Test** — `CELERY_TASK_ALWAYS_EAGER = True` runs tasks synchronously in tests. Call task directly, assert side effects

## Signals vs Tasks

All signal handlers run **synchronously in the request** (`_update_operator_hours`, `_recompute_qualification`, `on_audit_save`). Only exception: `RegulationFacilityMapping.save()` queues `recompute_appendix_k_flags.delay()` async. See **operator-qualification-lifecycle** skill for signal details.

## Import Task Architecture

See the **excel-import-system** skill for full import details. Key points:
- `execute_import(job_id)` routes to 4 type handlers
- Performance audits use `objects.create()` individually (signals required)
- Other types use `bulk_create` + manual signal handler calls
- Views use `CELERY_TASK_ALWAYS_EAGER` check for sync/async dispatch

## Common Mistakes

- **Adding beat entries to both `celery.py` and `base.py`** — duplicates the schedule. Use `base.py` only
- **Forgetting per-company try/except** in batch tasks — one company failure kills the entire task
- **Using `self.retry()` without `bind=True`** — `self` is only available with `bind=True` decorator
- **Testing retry logic in eager mode** — `CELERY_TASK_EAGER_PROPAGATES = True` means exceptions propagate immediately, bypassing retry
- **Calling signal handler functions from tasks** is fine (e.g., `_update_operator_hours()`) — but know that `bulk_create` bypasses signals, so you must call handlers manually
- **Assuming `.delay()` works in tests** — it does, but runs synchronously via eager mode. No actual Redis queue in tests


## Amendments
