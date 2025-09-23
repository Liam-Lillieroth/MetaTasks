# Dynamic Work Item Forms

Summary:
- Forms adapt per-workflow based on `Workflow.field_config`
- Replacement fields use `replacement_{name}` and values stored in `WorkItem.data`
- Templates conditionally render fields when present in the form

How to test:
- Configure a workflow fields → open work item creation → verify visible fields
