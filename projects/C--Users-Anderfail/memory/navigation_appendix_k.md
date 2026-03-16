---
name: navigation_appendix_k
description: Key file locations and code paths in the Appendix K compliance management system
type: navigation
---

**Backend apps:** `appendix_k/apps/` — 10 apps: core, tenants, accounts, facilities, operators, surveys, imports, compliance, notifications, support

**Signal handlers (most important for bugs):**
- Survey hours: `apps/surveys/signals.py` → `_update_operator_hours()`
- Training qualification: `apps/operators/signals.py` → `_recompute_qualification()`
- Audit pass/fail + suspension: `apps/operators/signals.py` → `on_audit_save`
- Regulation mapping cache: `apps/surveys/signals.py` → `invalidate_mapping_cache()`

**Approval workflow:**
- Views: `apps/operators/approval_views.py` → `ApprovalQueueView`, `BulkApprovalView`
- URL patterns: `approve/`, `reject/`, `resubmit/` on training-records and audits
- Permissions: `apps/core/permissions.py` → `can_approve_training()`, `can_approve_audit()`, `_user_is_senior()`
- Phase constants: `SENIOR_APPROVAL_PHASES`, `MANAGER_APPROVAL_PHASES` in `apps/core/permissions.py`
- Frontend: `pages/approvals/ApprovalsPage.tsx`, `components/common/ApprovalBadge.tsx`, `components/common/ApprovalActions.tsx`

**Compliance checks:** `apps/compliance/checks.py` — 6 check functions, called nightly by Celery beat at 2:00 AM

**Import pipeline:** `apps/imports/parser.py` (Excel parsing + sanitization), `apps/imports/tasks.py` (execution + regulation overrides)

**Frontend pages:** `frontend/src/pages/` — lazy-loaded except LoginPage
**Frontend stores:** `frontend/src/stores/` — authStore, themeStore, uiStore (Zustand)
**Responsive hooks:** `frontend/src/hooks/` — useMediaQuery, useSwipeAction, usePullToRefresh
**Mobile components:** `frontend/src/components/common/` — BottomTabBar, BottomSheet, MobileListCard, SwipeableTabs, ComplianceStatusCard

**Config:** `config/settings/base.py` (Celery beat schedule, CORS, JWT, etc.)
**Docker:** `docker-compose.yml` (6 services: db, redis, backend, celery_worker, celery_beat, frontend)

## Connections
- Related: [[compliance-checks]], [[multi-tenant-patterns]], [[operator-qualification-lifecycle]], [[frontend-architecture]], [[compliance-audit]], [[security-review]]
- Tags: #navigation #appendix-k
