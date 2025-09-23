# Transition Customization (Design)

Schema additions (WorkflowTransition):
- Visual: `color`, `icon`, `description`
- Behavior: `requires_confirmation`, `confirmation_message`, `requires_comment`, `comment_prompt`, `auto_assign_to_step_team`
- Access: `permission_level`, `is_active`, `order`

Forms:
- `WorkflowTransitionForm` supports conditional fields and live preview
- Bulk creation supports predefined patterns and custom JSON input

Runtime:
- `can_user_execute(user_profile, work_item)` enforces permission logic
- Template tags filter available transitions per user

Migration: safe migration with defaults to preserve existing transitions
