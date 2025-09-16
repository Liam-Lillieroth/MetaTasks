#!/usr/bin/env python
"""
Debug script to test mentions functionality by simulating DOM interaction.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediap.settings')
sys.path.append('.')
django.setup()

from django.test import Client
from core.models import UserProfile
from services.cflows.models import WorkItem

def test_mentions_dom_elements():
    print("Testing mentions DOM elements and script functionality...")
    
    # Get a test user and work item
    up = UserProfile.objects.select_related("user", "organization").first()
    if not up:
        print("✗ No user profile found")
        return False
        
    wi = WorkItem.objects.filter(workflow__organization=up.organization).first()
    if not wi:
        print("✗ No work item found")
        return False
        
    c = Client()
    c.force_login(up.user)
    
    # Get work item detail page
    resp = c.get(f"/services/cflows/work-items/{wi.id}/")
    if resp.status_code != 200:
        print(f"✗ Work item page failed: {resp.status_code}")
        return False
        
    content = resp.content.decode('utf-8')
    
    # Check for required DOM elements
    checks = [
        ('Form element', 'id="add-comment-form"'),
        ('Dropdown element', 'id="mention-suggestions"'),
        ('Textarea field', 'name="content"'),
        ('Script block', 'querySelector(\'textarea[name="content"]\')'),
        ('API URL', 'api/mentions/suggestions'),
        ('Event listener', 'addEventListener(\'input\''),
    ]
    
    all_passed = True
    for check_name, search_text in checks:
        if search_text in content:
            print(f"✓ {check_name} found")
        else:
            print(f"✗ {check_name} missing: {search_text}")
            all_passed = False
    
    # Test the API endpoint directly
    mentions_resp = c.get("/services/cflows/api/mentions/suggestions/?q=test")
    if mentions_resp.status_code == 200:
        print("✓ Mentions API accessible")
        data = mentions_resp.json()
        if 'users' in data and 'teams' in data:
            print(f"  - Response has users ({len(data['users'])}) and teams ({len(data['teams'])})")
        else:
            print(f"  - Response structure: {list(data.keys())}")
    else:
        print(f"✗ Mentions API failed: {mentions_resp.status_code}")
        all_passed = False
    
    # Check if textarea has the right attributes
    if 'class="w-full px-3 py-2 border border-gray-300' in content:
        print("✓ Textarea has expected CSS classes")
    else:
        print("✗ Textarea styling may be missing")
        all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success = test_mentions_dom_elements()
    if success:
        print("\n✓ All basic checks passed. Issue may be in client-side execution.")
        print("Suggestions:")
        print("1. Check browser console for JavaScript errors")
        print("2. Verify the mentions script is running after DOM load")
        print("3. Test typing '@' in the comment textarea")
    else:
        print("\n✗ Some checks failed. Fix these issues first.")
    
    sys.exit(0 if success else 1)