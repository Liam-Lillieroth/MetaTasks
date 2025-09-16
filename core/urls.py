from django.urls import path, include
from . import views
from . import notification_views

app_name = 'core'

urlpatterns = [
    path('check-organization/', views.check_organization_access, name='check_organization_access'),
    path('create-personal-org/', views.create_personal_organization, name='create_personal_organization'),
    path('setup/', views.setup_organization, name='setup_organization'),
    
    # Notifications
    path('notifications/', notification_views.notification_center, name='notification_center'),
    path('notifications/api/', notification_views.notification_api, name='notification_api'),
    path('notifications/preferences/', notification_views.notification_preferences, name='notification_preferences'),
    path('notifications/<int:notification_id>/read/', notification_views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:notification_id>/delete/', notification_views.delete_notification, name='delete_notification'),
    
    # Role Management
    path('roles/', include('core.role_urls')),
    
    # User Management
    path('users/', include('core.user_management_urls', namespace='user_management')),
]
