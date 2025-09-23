# Staff Panel Service

Purpose: Administrative interface for organization settings, roles, teams, integrations, and audit logs.

Features:
- Role & permission management (full CRUD)
- Team management and member assignment
- Integration configuration and monitoring
- Advanced system logs with filtering and export
- Standalone service under `services/staff_panel/` with its own base template

Access URLs:
- `/services/staff-panel/` — dashboard
- `/services/staff-panel/roles/`
- `/services/staff-panel/teams/`
- `/services/staff-panel/integrations/`
- `/services/staff-panel/logs/`

Notes:
- Staff panel is migrated to its own service and uses organization-scoped access control.
