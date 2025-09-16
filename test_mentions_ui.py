#!/usr/bin/env python
"""
Quick test script to verify mentions UI setup
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediap.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import UserProfile, Organization

def test_mentions_ui():
    print("Testing mentions UI setup...")
    
    # Create a test client
    client = Client()
    
    # Get a test user (assuming we have one)
    try:
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("ERROR: No active users found")
            return False
            
        profile = UserProfile.objects.filter(user=user).first()
        if not profile:
            print("ERROR: No user profile found")
            return False
            
        print(f"Using user: {user.username}")
        print(f"Organization: {profile.organization.name if profile.organization else 'None'}")
        
        # Log in the user
        client.force_login(user)
        
        # Try to access a work item detail page
        from services.cflows.models import WorkItem
        work_item = WorkItem.objects.filter(workflow__organization=profile.organization).first()
        if not work_item:
            print("ERROR: No work items found")
            return False
            
        print(f"Testing with work item: {work_item.title}")
        
        # Make the request
        response = client.get(f'/services/cflows/work-items/{work_item.id}/')
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for mentions script elements
            checks = [
                ('form with id add-comment-form', 'id="add-comment-form"' in content),
                ('mentions dropdown element', 'id="mention-suggestions"' in content),
                ('mentions script', 'getCurrentMention' in content),
                ('DOMContentLoaded wrapper', 'DOMContentLoaded' in content),
                ('input event listener', "addEventListener('input'" in content),
                ('API URL template', 'api_mention_suggestions' in content),
            ]
            
            print("\nContent checks:")
            for name, result in checks:
                status = "✓" if result else "✗"
                print(f"  {status} {name}")
            
            # Check if comment form is in the response
            if '{{ comment_form.content }}' in content:
                print("  ✗ Comment form not rendered (still showing template syntax)")
            elif 'textarea' in content:
                print("  ✓ Textarea element found in response")
            else:
                print("  ✗ No textarea element found")
                
            return all(result for _, result in checks)
        else:
            print(f"ERROR: Failed to load page (status {response.status_code})")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == '__main__':
    success = test_mentions_ui()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)