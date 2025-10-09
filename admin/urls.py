from django.urls import path
from core.health_views import system_health_check

urlpatterns = [
    path('health-check/', system_health_check, name='system_health_check'),
]