---
name: frontend-architecture
description: Use when adding React pages, components, API endpoints, routes, or working with the frontend auth system, state management, or UI patterns in the Appendix K frontend
---

# Frontend Architecture

## Overview

React 18 + TypeScript + Vite + Tailwind CSS SPA. Zustand for auth state, React Query for server state. Axios client with JWT auto-refresh. Lazy-loaded routes with role-based access via `RequireRole`.

## Key Files

- `frontend/src/App.tsx` — all routes, lazy loading, `RequireRole` wrappers
- `frontend/src/api/client.ts` — Axios instance with JWT interceptors
- `frontend/src/api/endpoints.ts` — all API functions grouped by domain
- `frontend/src/api/auth.ts` — login, logout, token refresh
- `frontend/src/stores/authStore.ts` — Zustand auth state (user, login, logout, loadUser)
- `frontend/src/utils/types.ts` — TypeScript interfaces for all API models
- `frontend/src/components/auth/RequireRole.tsx` — route-level role guard

## Stack

React 18, TypeScript 5.3, Vite 5, Tailwind CSS 3.3, React Router 6, @tanstack/react-query 5, Zustand 4, Axios 1.6, Recharts 2, @heroicons/react 2, react-hot-toast 2.

## Directory Structure

```
frontend/src/
├── api/           # client.ts, endpoints.ts, auth.ts
├── stores/        # authStore.ts, uiStore.ts, themeStore.ts
├── hooks/         # useDebounce.ts
├── utils/         # types.ts
├── components/
│   ├── auth/      # RequireRole.tsx
│   ├── common/    # DataTable, Pagination, SearchInput, StatusBadge, etc.
│   ├── forms/     # SurveyForm, OperatorForm, TrainingRecordForm, etc.
│   └── layout/    # AppShell, Header, Sidebar
└── pages/
    ├── auth/      # LoginPage, AccountPage, ChangePasswordPage, AcceptInvitePage
    ├── dashboard/  # DashboardPage
    ├── operators/  # OperatorsListPage, OperatorDetailPage
    ├── facilities/ # FacilitiesListPage, FacilityDetailPage
    ├── surveys/    # SurveysListPage
    ├── compliance/ # ComplianceAlertsPage
    ├── imports/    # ImportPage
    └── admin/      # UsersPage, CompanyPage, CompaniesPage, NotificationSettingsPage, RegulationMappingPage
```

## Auth Flow

JWT tokens in `localStorage`. Axios request interceptor adds `Authorization: Bearer`. Response interceptor catches 401 → auto-refreshes (concurrent 401s share one refresh promise). Failed refresh → clears tokens → `/login`.

## API Client Pattern

All API calls go through `api/endpoints.ts` — **never call `api.get()`/`api.post()` directly from components.**

```typescript
// api/endpoints.ts — grouped by domain
export const operatorsApi = {
  list: (params?) => api.get<PaginatedResponse<Operator>>('/operators/', { params }),
  get: (id: string) => api.get<Operator>(`/operators/${id}/`),
  create: (data) => api.post<Operator>('/operators/', data),
  update: (id, data) => api.patch<Operator>(`/operators/${id}/`, data),
};
```

**File uploads** use `FormData` with `'Content-Type': 'multipart/form-data'` header.

## Adding a New Page

1. **Create page** at `pages/myfeature/MyFeaturePage.tsx` — default export (required for lazy loading)
2. **Add API functions** to `api/endpoints.ts` — follow existing domain grouping pattern
3. **Add types** to `utils/types.ts`
4. **Add route** to `App.tsx` — use `lazy()` import + `Suspense` + `RequireRole` wrapper
5. **Add nav link** to `components/layout/Sidebar.tsx`

Verify the backend API endpoint exists in `urls.py` before building the page.

## Route Access Control

| Route Pattern | Access |
|--------------|--------|
| `/login`, `/invite/:token` | Public |
| `/`, `/operators`, `/facilities`, `/surveys`, `/compliance` | All authenticated |
| `/imports` | Manager+ |
| `/admin/users`, `/admin/company`, `/admin/regulations`, `/admin/notifications` | Admin+ |
| `/admin/companies` | Superadmin only |

Use `<RequireRole roles={[...]}>{children}</RequireRole>` wrapper.

## Common Reusable Components

All in `components/common/`: `DataTable` (sortable, paginated), `Pagination`, `SearchInput` (debounced), `StatusBadge`, `FilterChips`, `FileUpload` (drag-drop), `ConfirmDialog`, `Breadcrumbs`, `ErrorBoundary`.

## Common Mistakes

- **Importing `api` directly instead of using `endpoints.ts`** — breaks the API abstraction layer
- **Forgetting `Suspense` wrapper** on lazy-loaded routes — React will throw
- **Forgetting `RequireRole` on admin routes** — any authenticated user can access
- **Not adding types to `utils/types.ts`** — TypeScript errors propagate to all consumers
- **Using `useEffect` for data fetching** instead of React Query — loses caching, deduplication, and loading states
- **Storing server data in Zustand** — use React Query for server state, Zustand for client-only state (auth, UI preferences, theme)
- **Hardcoding `/api/v1/` in components** — always use the Axios instance from `client.ts` (baseURL handles the prefix)
- **Adding frontend API calls without verifying backend endpoints exist** — check `urls.py` and the DRF router to confirm the endpoint is wired before building the page
- **Not wrapping pages with `ErrorBoundary`** — the `ErrorBoundary` component exists in `components/common/`. Use it around page content that fetches data to prevent full-app crashes


## Amendments
