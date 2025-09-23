# Field Customization (Design)

Purpose: Allow per-workflow control of standard fields and replacement with custom fields.

Configuration:
- `Workflow.field_config` stores JSON with keys for standard fields (title, description, priority, tags, due_date, estimated_duration)
- `get_active_fields()` merges defaults and workflow overrides

Form behavior:
- `WorkItemForm` reads workflow config and shows/hides fields
- Replacement fields are added as `replacement_{field_name}` and stored in `WorkItem.data`

UI:
- Interactive configuration page with toggle per field and replacement dropdown

Future: step-specific configs and conditional display rules
