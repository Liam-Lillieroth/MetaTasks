#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediap.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

# Test authentication
User = get_user_model()
client = Client()

# Login
login_response = client.login(username='demoadmin', password='pass')
print(f"Login successful: {login_response}")

# Test notification API
api_response = client.get('/core/notifications/api/')
print(f"API Response status: {api_response.status_code}")
print(f"API Response content: {api_response.content.decode()}")

# Check if user exists and has notifications
try:
    user = User.objects.get(username='demoadmin')
    print(f"User found: {user.username}")
    print(f"User notifications count: {user.notifications.count()}")
    print(f"Unread notifications: {user.notifications.filter(is_read=False).count()}")
except User.DoesNotExist:
    print("User 'demoadmin' not found")