---
name: project_mobile_initiative
description: Appendix K mobile/tablet field access initiative - PWA approach with 4 sub-projects, offline sync for remote field sites
type: project
---

Mobile/tablet field access for the Appendix K Compliance Management System.

**Why:** Operators and managers need to log training records and performance audits in the field. Facilities are across the US with mixed connectivity (some sites have no cell/wifi). Devices are a mix of company-issued tablets and BYOD phones (iOS/Android).

**How to apply:**
- Architecture: PWA enhancement of existing React+Tailwind app (not native or hybrid)
- Sub-project 1: Responsive & touch optimization (spec complete: `docs/superpowers/specs/2026-03-13-responsive-touch-optimization-design.md`)
- Sub-project 2: Approval workflow (training records need senior/manager sign-off, review queue)
- Sub-project 3: PWA infrastructure (service worker, manifest, installability)
- Sub-project 4: Offline sync (IndexedDB queue, background sync, conflict resolution)
- Key new business feature: Approval workflow -- training records created as "pending approval", seniors approve observing/performing-with-senior phases, managers approve classroom/independent/final test, seniors approve all performance audits
- Surveys are NOT tracked on mobile -- they come from external systems (LeakTracker Pro etc.)

## Connections
- Related: [[frontend-architecture]], [[appendix-k-board]]
- Tags: #project #appendix-k #mobile
