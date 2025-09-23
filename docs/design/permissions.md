# Permission System (Design)

Summary:
- Central `PermissionService` with `has_permission()` and helper messages
- Decorator `@require_permission` for views
- Template tags: `has_permission` and `permission_button`
- 34 default permissions and role templates (Admin, Manager, Team Lead, Member)

Best practices:
- Check permissions server-side (decorators) and client-side (template tags)
- Use organization scoping for all checks
- Provide user-friendly messages when actions are blocked
