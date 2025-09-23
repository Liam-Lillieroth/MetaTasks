# Backward Transitions

Summary:
- Authorized users can move work items back to previously visited steps
- Requires comment and produces audit trail entries
- Permissioned: org admins, staff, or item creators (configurable)

UI:
- "Move Back" button with dropdown of available previous steps
- Confirmation dialog with required comment

Developer notes:
- Uses `WorkItemHistory` to determine valid targets
- Views: `backward_transition_form`, `move_work_item_back`
