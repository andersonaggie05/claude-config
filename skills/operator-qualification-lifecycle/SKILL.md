---
name: operator-qualification-lifecycle
description: Use when working with operator qualification status transitions, training records, performance audits, the signal-driven recomputation system, or cached operator fields
---

# Operator Qualification Lifecycle

## Overview

Operators follow a state machine driven by Django signals. Training records, performance audits, and survey hours each trigger recomputation of qualification status and cached fields. Understanding the signal chain is critical — incorrect modifications can corrupt operator state across the system.

## Key Files

- `apps/operators/models.py` — Operator, TrainingRecord (11 phases), PerformanceAudit
- `apps/operators/signals.py` — `_recompute_qualification()`, audit failure tracking, `PHASE_MINIMUM_HOURS`, `RETRAIN_MINIMUM_HOURS`
- `apps/surveys/signals.py` — `_update_operator_hours()`, senior promotion/demotion
- `apps/operators/serializers.py` — API-level validation, `PHASE_PREREQUISITES`

## State Machine

```
in_training ──→ qualified ──→ senior
                    ↑              │
                    │       (12mo hours < 40)
                    │              ↓
                    ├──── qualified ←──┘
                    │
               (retrained)
                    ↑
                suspended ←── (>=2 consecutive audit failures)
                    ↑
            qualified OR senior

inactive (terminal, excluded from all recomputation)
```

**Transitions:**
- `in_training → qualified`: All 5 initial phases completed with minimum hours + passed final test
- `qualified → senior`: Career >= 1400h AND rolling 12mo >= 40h
- `senior → qualified`: Rolling 12mo drops below 40h (auto-demotion)
- `qualified/senior → suspended`: 2+ consecutive audit failures (NOT 3)
- `suspended → qualified`: All 3 retrain phases completed with hour minimums + passed retrain final test (resets consecutive failures to 0)

## Training Phase Minimum Hours

### Initial Training (signals.py `PHASE_MINIMUM_HOURS`)

All 5 phases required: `classroom_initial`, `observing_senior`, `performing_with_senior`, `performing_independent`, `final_test`. Note: `classroom_initial` has no hour minimum in `PHASE_MINIMUM_HOURS` but MUST exist as a completed, compliant record.

| Phase | Min Hours |
|-------|-----------|
| `classroom_initial` | (none enforced — but phase required) |
| `observing_senior` | 3 |
| `performing_with_senior` | 12 |
| `performing_independent` | 15 |
| `final_test` | 2 |

### Retraining After Suspension (`RETRAIN_MINIMUM_HOURS`)

| Phase | Min Hours |
|-------|-----------|
| `retrain_with_senior` | 8 |
| `retrain_independent` | 8 |
| `retrain_final_test` | 2 |

**Total retraining: 18 hours minimum.**

## Final Test / Audit Pass Criteria

Same logic in `TrainingRecord.evaluate_final_test()` and `PerformanceAudit.evaluate_pass()`:

- **>= 10 leaks found by senior/auditor**: Trainee/operator miss rate must be <= 10%
- **< 10 leaks found**: Must miss exactly 0

## Signal Chains

### Survey Save/Delete → `_update_operator_hours()`

Updates 5 cached fields: `career_survey_hours`, `rolling_12mo_survey_hours`, `appendix_k_career_hours`, `appendix_k_12mo_hours`, `last_survey_date`. Also handles:
- **Senior promotion**: `qualified` + career >= 1400 + 12mo >= 40 → `senior`
- **Senior demotion**: `senior` + 12mo < 40 → `qualified`

**Note:** Suspended operators accumulate hours but are NOT promoted/demoted. The signal only checks `qualified` and `senior` statuses.

### TrainingRecord Save → `_recompute_qualification()`

1. Evaluates final test result (if `final_test` or `retrain_final_test` phase)
2. Updates `last_classroom_training_date` (for classroom phases only)
3. Recomputes qualification status:
   - `inactive` → no change (early return)
   - `suspended` → check if all 3 retrain phases complete with hour minimums → restore to `qualified` (NOT senior — see Re-Promotion below)
   - Otherwise → check if all 5 initial phases complete with hours + passed final test → `qualified` or `senior`

### PerformanceAudit Save → Audit Tracking

1. Evaluates pass/fail via `evaluate_pass()`
2. Updates `last_performance_audit_date`
3. Computes consecutive failures from 2 most recent audits
4. If consecutive failures >= 2 → sets `qualification_status = 'suspended'`

**Serializer side effect:** `PerformanceAuditSerializer.create()` also creates a `ComplianceAlert` directly (not via the idempotent `_create_or_update_alert` pattern) when an audit fails. This means API-created failed audits generate duplicate alerts alongside the nightly compliance check. The serializer also enforces: 3-month minimum spacing between audits and 2-hour minimum audit duration (API-only, not at model level).

## Cached Fields on Operator

| Field | Updated By | Trigger |
|-------|-----------|---------|
| `career_survey_hours` | `_update_operator_hours` | Survey save/delete |
| `rolling_12mo_survey_hours` | `_update_operator_hours` | Survey save/delete |
| `appendix_k_career_hours` | `_update_operator_hours` | Survey save/delete |
| `appendix_k_12mo_hours` | `_update_operator_hours` | Survey save/delete |
| `last_survey_date` | `_update_operator_hours` | Survey save/delete |
| `last_classroom_training_date` | `on_training_record_save` | TrainingRecord save |
| `last_performance_audit_date` | `on_audit_save` | PerformanceAudit save |
| `consecutive_audit_failures` | `on_audit_save` | PerformanceAudit save |
| `qualification_status` | All three signal handlers | Any of the above |

## Known Architectural Issues

### Dual-Write on Audit Creation via API

The serializer and signal BOTH modify operator state with different logic:
- **Signal**: Recalculates consecutive failures from 2 most recent audits (`[:2]` slice)
- **Serializer**: Increments counter from existing value

The signal fires twice per serializer-driven audit creation (once from `super().create()`, once from `audit.save(update_fields=['passed'])`). The serializer's `save(update_fields=[...])` is the final write.

For direct ORM creation (`PerformanceAudit.objects.create()`), only the signal runs — different result than API path. Tests use direct ORM.

### No Sequential Enforcement on Retrain Phases

`PHASE_PREREQUISITES` in the serializer covers only initial training, not retraining. Retrain phases can be completed in any order. `_recompute_qualification()` only checks that all 3 exist — it doesn't enforce sequence.

### Classroom Date Not Updated by Retrain Phases

The `last_classroom_training_date` update only fires for `classroom_initial`, `classroom_biennial`, `refresher_retrain`, `full_retrain`. The retrain phases (`retrain_with_senior`, `retrain_independent`, `retrain_final_test`) do NOT update this field.

## Re-Promotion After Retraining

Retraining restores an operator to `qualified`, NOT `senior`. The `_recompute_qualification()` function returns early after the suspended→qualified restoration (line 137) and never reaches the senior check. Re-promotion to senior requires a subsequent event: a Survey save triggers `_update_operator_hours()` which checks `qualified` + career >= 1400 + 12mo >= 40 → `senior`.

## Operator Transfer

`apps/core/transfer_utils.py`: Creates new Operator at target company, marks old as `inactive`, preserves `tracking_id` via `transferred_from` FK. Career hours at time of transfer are recorded in `OperatorTransfer` model.

## Common Mistakes

- Assuming suspension requires 3 failures — the threshold is 2 (`CONSECUTIVE_FAILURE_LIMIT = 2`)
- Modifying operator fields in a serializer without accounting for signal-driven changes (last writer wins based on execution order)
- Forgetting that survey signals handle senior promotion/demotion — don't duplicate this logic elsewhere
- Expecting retrain phases to be enforced sequentially — they're only verified at the aggregate level during restoration
- Modifying training phase hour requirements without understanding the EPA Appendix K mandate
- Creating PerformanceAudit via ORM vs API produces different consecutive failure counts (signal recalculation vs serializer increment)


## Amendments
