#!/usr/bin/env python
"""
Test mentions API data availability
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediap.settings')
sys.path.append('.')
django.setup()

from django.test import Client
from core.models import UserProfile, Team

def test_mentions_data():
    print("Testing mentions API data availability...")
    
    # Get a test user
    up = UserProfile.objects.select_related("user", "organization").first()
    if not up:
        print("✗ No user profile found")
        return False
        
    org = up.organization
    print(f"Organization: {org.name} (ID: {org.id})")
    
    # Check users in organization
    users_in_org = UserProfile.objects.filter(
        organization=org,
        user__is_active=True
    ).select_related('user')
    
    print(f"Users in organization: {users_in_org.count()}")
    for user_profile in users_in_org[:5]:
        print(f"  - {user_profile.user.username} ({user_profile.user.get_full_name() or 'No name'})")
    
    # Check teams in organization
    teams_in_org = Team.objects.filter(
        organization=org,
        is_active=True
    )
    
    print(f"Teams in organization: {teams_in_org.count()}")
    for team in teams_in_org[:5]:
        print(f"  - {team.name}")
    
    # Test the API with different queries
    c = Client()
    c.force_login(up.user)
    
    test_queries = ['', 'a', 'admin', 'team']
    
    for query in test_queries:
        resp = c.get(f"/services/cflows/api/mentions/suggestions/?q={query}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Query '{query}': {len(data.get('users', []))} users, {len(data.get('teams', []))} teams")
            if data.get('users'):
                print(f"  First user: {data['users'][0]}")
            if data.get('teams'):
                print(f"  First team: {data['teams'][0]}")
        else:
            print(f"Query '{query}' failed: {resp.status_code}")
    
    return True

if __name__ == "__main__":
    test_mentions_data()