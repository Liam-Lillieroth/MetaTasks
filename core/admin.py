from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Organization, UserProfile, Team, JobType, CalendarEvent
from .permissions import Permission, Role, RolePermission, UserRoleAssignment


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'user_count', 'team_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            user_count=Count('members', distinct=True),
            team_count=Count('teams', distinct=True)
        )
    
    def user_count(self, obj):
        return obj.user_count
    user_count.short_description = 'Users'
    user_count.admin_order_field = 'user_count'
    
    def team_count(self, obj):
        return obj.team_count
    team_count.short_description = 'Teams'
    team_count.admin_order_field = 'team_count'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'organization', 'title', 'department', 'is_active']
    list_filter = ['organization', 'is_organization_admin', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'department']
    raw_id_fields = ['user', 'organization']
    readonly_fields = ['created_at', 'updated_at']
    
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Full Name'
    full_name.admin_order_field = 'user__first_name'


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'member_count', 'has_bookings_indicator', 'is_active']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['members']
    actions = ['check_team_integrity', 'add_org_admin_to_empty_teams']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(members_count=Count('members'))
    
    def member_count(self, obj):
        return obj.members_count if hasattr(obj, 'members_count') else obj.member_count
    member_count.short_description = 'Members'
    member_count.admin_order_field = 'members_count'
    
    def has_bookings_indicator(self, obj):
        has_bookings = obj.has_active_bookings()
        member_count = obj.members.filter(is_active=True).count()
        
        if has_bookings and member_count == 0:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Has bookings but no members!</span>')
        elif has_bookings:
            return format_html('<span style="color: green;">✓ Has bookings</span>')
        else:
            return format_html('<span style="color: gray;">No bookings</span>')
    has_bookings_indicator.short_description = 'Booking Status'
    
    def check_team_integrity(self, request, queryset):
        """Check selected teams for integrity issues"""
        issues = []
        for team in queryset:
            if team.has_active_bookings():
                member_count = team.members.filter(is_active=True).count()
                if member_count == 0:
                    issues.append(f"Team '{team.name}' has bookings but no active members")
        
        if issues:
            self.message_user(request, f"Found {len(issues)} integrity issues:\n" + "\n".join(issues), level='WARNING')
        else:
            self.message_user(request, "No integrity issues found in selected teams", level='SUCCESS')
    
    check_team_integrity.short_description = "Check selected teams for integrity issues"
    
    def add_org_admin_to_empty_teams(self, request, queryset):
        """Add organization admin to teams that have bookings but no members"""
        fixed_count = 0
        for team in queryset:
            if team.has_active_bookings():
                member_count = team.members.filter(is_active=True).count()
                if member_count == 0:
                    # Find organization admin
                    org_admins = team.organization.members.filter(
                        is_organization_admin=True,
                        is_active=True
                    )
                    if org_admins.exists():
                        admin = org_admins.first()
                        team.members.add(admin)
                        fixed_count += 1
        
        if fixed_count > 0:
            self.message_user(request, f"Added organization admin to {fixed_count} teams", level='SUCCESS')
        else:
            self.message_user(request, "No teams needed fixing", level='INFO')
    
    add_org_admin_to_empty_teams.short_description = "Add org admin to teams with bookings but no members"


@admin.register(JobType)
class JobTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'default_duration_hours', 'color_preview', 'is_active']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'description']
    
    def color_preview(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; color: white; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color
        )
    color_preview.short_description = 'Color'


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'event_type', 'start_time', 'end_time', 'created_by', 'color_preview']
    list_filter = ['organization', 'event_type', 'is_all_day', 'start_time', 'related_team']
    search_fields = ['title', 'description']
    raw_id_fields = ['created_by', 'related_team']
    filter_horizontal = ['invitees']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    
    def color_preview(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; color: white; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color
        )
    color_preview.short_description = 'Color'


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'category', 'service', 'is_global', 'requires_resource']
    list_filter = ['category', 'service', 'is_global', 'requires_resource']
    search_fields = ['name', 'codename', 'description']
    readonly_fields = ['created_at']


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0
    raw_id_fields = ['permission', 'granted_by']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'role_type', 'is_active', 'is_default', 'user_count']
    list_filter = ['organization', 'role_type', 'is_active', 'is_default']
    search_fields = ['name', 'description']
    raw_id_fields = ['organization', 'created_by', 'inherits_from']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [RolePermissionInline]
    
    def user_count(self, obj):
        return obj.get_user_count()
    user_count.short_description = 'Users'


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'resource_type', 'granted_by', 'granted_at']
    list_filter = ['role__organization', 'permission__category', 'granted_at']
    search_fields = ['role__name', 'permission__name']
    raw_id_fields = ['role', 'permission', 'granted_by']
    readonly_fields = ['granted_at']


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'role', 'is_active', 'valid_from', 'valid_until', 'assigned_at']
    list_filter = ['role__organization', 'is_active', 'assigned_at']
    search_fields = ['user_profile__user__username', 'role__name']
    raw_id_fields = ['user_profile', 'role', 'assigned_by']
    readonly_fields = ['assigned_at']
