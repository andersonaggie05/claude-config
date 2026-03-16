---
name: Security Review
description: Security-only review covering multi-tenant isolation, input validation, signal safety, and OWASP checks
type: knowledge-module
source: C:/Users/Anderfail/.claude/skills/agent-pipelines/SKILL.md + C:/Users/Anderfail/.claude/skills/multi-tenant-patterns/SKILL.md
---

# Security Review

Review for security concerns only. Do NOT review code quality, readability, or design patterns — those are separate concerns. Scope is strictly: multi-tenant isolation, input validation, signal safety, and OWASP-relevant vulnerabilities.

## Multi-Tenant Isolation

Every tenant-scoped model, view, and serializer must be verified against three isolation layers.

### Layer 1: Model

All tenant-scoped models must extend `TenantModel` (company FK + `TenantManager`). Unique constraints must include `company` — a constraint on `employee_id` alone would collide across tenants.

**Check**: Does the model extend `TenantModel`? Does every `UniqueConstraint` include `company`?

### Layer 2: View

Every `ModelViewSet` and `GenericAPIView` for tenant data must use `TenantViewMixin`. Raw `APIView` subclasses have no automatic scoping — they require an explicit `company` filter in every method.

**Check for leaks**:
- `ModelViewSet` without `TenantViewMixin` → leaks all company data to any authenticated user
- `APIView` without `if request.user.role == 'superadmin'` / `filter(company=request.user.company)` → leaks cross-tenant
- `.objects.all()` in a view without `[IsSuperAdmin]` permission → leaks all tenants
- Missing `perform_create` override → new records get no company assignment

**Superadmin handling**: Superadmins have `company=NULL`. Always check role before accessing `request.user.company`.

### Layer 3: Object Permission

`IsCompanyMember` verifies `obj.company == request.user.company` at the object level. Use alongside `TenantViewMixin` for defense in depth.

### Serializer Validation

Related field querysets must be scoped to the tenant via `TenantSerializerMixin`. Uniqueness validation must also scope to company:
```python
qs = MyModel.objects.filter(company=company, field=value)
if self.instance:
    qs = qs.exclude(pk=self.instance.pk)
```

## Signal Safety

Signal handlers that update shared state must prevent race conditions:
- Use `select_for_update()` to lock the row before reading
- Wrap in `transaction.atomic()` to ensure atomicity
- Celery tasks must respect tenant boundaries — pass `company_id` explicitly, never rely on thread-local state

**Check**: Do signal handlers that modify operator state use `select_for_update()` + `transaction.atomic()`?

## Input Validation

Validate all inputs at system boundaries: user-submitted data, external API responses, file uploads (e.g., Excel imports).

**Check**:
- Are import files validated before execution? (Import validation must prevent execution before user review)
- Are serializer fields explicitly typed with appropriate validators?
- Are bulk operations protected from injection via raw query construction?

## OWASP Checks

For each change, verify:
- **Broken access control**: Can a non-admin reach admin-only endpoints? Can one tenant access another's data?
- **Injection**: Is user input ever passed to raw SQL, shell commands, or template rendering unsanitized?
- **Security misconfiguration**: Are debug flags, permissive CORS, or weak permissions present?
- **Sensitive data exposure**: Are API keys, tokens, or PII logged or returned in responses unnecessarily?

## Findings Format

Report security findings separately from code quality findings. Use severity levels:

- **CRITICAL**: Data leakage across tenants, authentication bypass, injection vulnerability
- **HIGH**: Missing permission check, unvalidated file execution, unprotected bulk operation
- **MEDIUM**: Defense-in-depth gap (e.g., missing object-level check when view-level exists), missing rate limiting
- **LOW**: Minor hardening opportunity

For each finding:
```
**[Severity]** — [Description]
- Location: [file:line]
- Impact: [What an attacker can do]
- Fix: [Specific remediation]
```

## Connections
- Depends on: [[completion-checklist]]
- Related skills: [[multi-tenant-patterns]] (full isolation pattern reference), [[compliance-audit]] (multi-tenant isolation is also a compliance control)
- Tags: #security #multi-tenant
