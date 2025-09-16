#!/usr/bin/env python
"""
Quick verification script to test the NoReverseMatch fixes.
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
from django.urls import reverse

def test_fixes():
    print("Testing URL namespace and mentions fixes...")
    
    # Test URL resolution
    try:
        url = reverse('cflows:api_mention_suggestions')
        print(f"✓ URL reverse works: {url}")
    except Exception as e:
        print(f"✗ URL reverse failed: {e}")
        return False
    
    # Test with authenticated client
    try:
        up = UserProfile.objects.select_related("user", "organization").first()
        if not up:
            print("✗ No user profile found for testing")
            return False
            
        wi = WorkItem.objects.filter(workflow__organization=up.organization).first()
        if not wi:
            print("✗ No work item found for testing")
            return False
            
        c = Client()
        c.force_login(up.user)
        
        # Test work item detail page
        resp = c.get(f"/services/cflows/work-items/{wi.id}/")
        if resp.status_code == 200:
            print(f"✓ Work Item {wi.id} page loads: {resp.status_code}")
        else:
            print(f"✗ Work Item page failed: {resp.status_code}")
            return False
            
        # Test mentions API
        mentions_resp = c.get("/services/cflows/api/mentions/suggestions/?q=a")
        if mentions_resp.status_code == 200:
            print(f"✓ Mentions API works: {mentions_resp.status_code}")
            data = mentions_resp.json()
            print(f"  - Users: {len(data.get('users', []))}")
            print(f"  - Teams: {len(data.get('teams', []))}")
        else:
            print(f"✗ Mentions API failed: {mentions_resp.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_fixes()
    sys.exit(0 if success else 1)