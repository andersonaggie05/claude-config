---
name: multi-tenant-patterns
description: Use when adding views, serializers, querysets, or models that must be scoped to a company tenant, or when working with cross-tenant superadmin views, permissions, or the TenantModel base class
---

# Multi-Tenant Patterns

## Overview

Every data model extends `TenantModel` (company FK) unless it is intentionally global. Forgetting the company filter leaks data across tenants. Three layers enforce isolation: model base class, view mixin, and object-level permission.

## Key Files

- `apps/core/models.py` — `TenantModel`, `TenantQuerySet`, `TenantManager`
- `apps/core/mixins.py` — `TenantViewMixin`, `TenantSerializerMixin`
- `apps/core/permissions.py` — `IsSuperAdmin`, `IsCompanyAdmin`, `IsManager`, `IsManagerOrReadOnly`, `IsCompanyMember`
- `apps/tenants/middleware.py` — `TenantMiddleware` (thread-local `get_current_company()`)

## Isolation Layers

### Layer 1: Model — `TenantModel`

```python
class TenantModel(TimestampedModel):
    company = models.ForeignKey('tenants.Company', on_delete=models.CASCADE,
                                related_name='%(class)ss')
    objects = TenantManager()  # provides .for_company(company)
```

All tenant-scoped models inherit this. UUID PKs, auto-timestamps, company FK.

**Unique constraints must include company:**
```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['company', 'employee_id'],
            condition=models.Q(employee_id__gt=''),
            name='unique_employee_id_per_company',
        ),
    ]
```

### Layer 2: View — `TenantViewMixin`

```python
class TenantViewMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'superadmin':
            return qs  # Superadmins see all
        return qs.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
```

**Use this on every ModelViewSet/GenericAPIView for tenant models.** It auto-filters querysets and auto-assigns company on create.

### Layer 3: Permission — `IsCompanyMember`

Object-level check: verifies `obj.company == request.user.company`. Use alongside `TenantViewMixin` for defense in depth.

## Role Hierarchy

| Role | Access Scope |
|------|-------------|
| `superadmin` | All companies (company=NULL on User) |
| `company_admin` | Own company — full CRUD |
| `manager` | Own company — full CRUD |
| `operator` | Own company — read own record only |
| `viewer` | Own company — read only |

**In views**, operators/viewers get additional filtering:
```python
if self.request.user.role in ('operator', 'viewer'):
    qs = qs.filter(user=self.request.user)
```

## Global (Non-Tenant) Models

These intentionally do NOT extend TenantModel:

| Model | Why Global |
|-------|-----------|
| `Company` | IS the tenant |
| `User` | Has company FK but not TenantModel (superadmins have company=NULL) |
| `Invitation` | Has company FK, uses direct filtering |
| `RegulationFacilityMapping` | EPA regulation data shared across all companies |
| `NotificationPreference` | Per-user, not per-company |

**Superadmin-only views** that query global data must use `permission_classes = [IsSuperAdmin]`.

## Adding a New Tenant-Scoped Endpoint

### Standard Pattern (ModelViewSet)

```python
class MyModelViewSet(TenantViewMixin, viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    permission_classes = [IsManagerOrReadOnly]
```

That's it. `TenantViewMixin` handles filtering and company assignment.

### Custom APIView (no queryset)

When you can't use `get_queryset()` (e.g., computed data, aggregations):

```python
class MyReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        if request.user.role == 'superadmin':
            qs = MyModel.objects.all()
        else:
            qs = MyModel.objects.filter(company=request.user.company)
        qs = qs.select_related('user', 'company')  # Avoid N+1
        # ... compute and return
```

**You must manually filter by company** — there is no mixin magic for raw APIViews. Also add `select_related`/`prefetch_related` yourself — `TenantViewMixin` doesn't set these either.

### Serializer Validation

Use `TenantSerializerMixin` for related field filtering:
```python
def get_tenant_queryset(self, model):
    request = self.context.get('request')
    if request and hasattr(request.user, 'company'):
        return model.objects.filter(company=request.user.company)
    return model.objects.none()
```

For uniqueness validation, always scope to company:
```python
qs = MyModel.objects.filter(company=company, field=value)
if self.instance:
    qs = qs.exclude(pk=self.instance.pk)
```

## Common Mistakes

- **Missing `TenantViewMixin`** on a ViewSet — leaks all company data to any authenticated user
- **Using `APIView` without manual company filter** — no automatic tenant scoping on raw APIViews
- **Unique constraint without company** — `unique_together = ['employee_id']` would block same ID across different companies
- **Using `.objects.all()` in a view** without `TenantViewMixin` or explicit filter — only safe with `[IsSuperAdmin]` permission
- **Forgetting `perform_create`** — if not using `TenantViewMixin`, new records get no company assignment
- **Using `.iterator()` with `prefetch_related`** — `.iterator()` defeats prefetch, causes N+1 queries. Use `.all()` instead for prefetched querysets
- **Assuming `request.user.company` exists** — superadmins have `company=NULL`; check role first


## Amendments
