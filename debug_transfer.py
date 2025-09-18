#!/usr/bin/env python3
"""
Debug script to test transfer permissions for any user
Usage: python debug_transfer.py <username> <work_item_uuid>
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/workspaces/MetaTasks')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediap.settings')
django.setup()

from accounts.models import CustomUser
from services.cflows.models import WorkItem

def test_transfer_permissions(username, work_item_uuid=None):
    try:
        user = CustomUser.objects.get(username=username)
        profile = user.mediap_profile
        
        print(f"=== Transfer Permission Debug for {username} ===")
        print(f"User: {user.username}")
        print(f"Profile: {profile}")
        print(f"Is org admin: {profile.is_organization_admin}")
        print(f"Has staff panel access: {profile.has_staff_panel_access}")
        print(f"Teams: {list(profile.teams.all())}")
        
        # Get work item
        if work_item_uuid:
            work_item = WorkItem.objects.get(uuid=work_item_uuid)
        else:
            work_item = WorkItem.objects.filter(is_completed=False).first()
        
        if not work_item:
            print("No work items found!")
            return
            
        print(f"\n=== Work Item Info ===")
        print(f"Title: {work_item.title}")
        print(f"UUID: {work_item.uuid}")
        print(f"Workflow: {work_item.workflow.name}")
        print(f"Owner team: {work_item.workflow.owner_team}")
        print(f"Created by: {work_item.created_by}")
        print(f"Current assignee: {work_item.current_assignee}")
        print(f"Is completed: {work_item.is_completed}")
        
        print(f"\n=== Transfer Check ===")
        transfer_check = work_item.can_transfer_to_workflow(profile)
        print(f"Can transfer: {transfer_check['can_transfer']}")
        print(f"Has permission: {transfer_check['has_permission']}")
        print(f"Has current access: {transfer_check['has_current_access']}")
        print(f"Can access destination: {transfer_check['can_access_destination']}")
        print(f"Reasons: {transfer_check['reasons']}")
        
        if transfer_check['can_transfer']:
            print(f"\n✅ TRANSFER BUTTON SHOULD BE VISIBLE")
            print(f"🔗 Work Item URL: http://localhost:8000/services/cflows/work-items/{work_item.uuid}/")
            print(f"🔗 Transfer URL: http://localhost:8000/services/cflows/work-items/{work_item.uuid}/transfer/")
        else:
            print(f"\n❌ TRANSFER BUTTON SHOULD BE HIDDEN")
            print(f"Reasons: {'; '.join(transfer_check['reasons'])}")
            
    except CustomUser.DoesNotExist:
        print(f"User '{username}' not found!")
        print("Available users:")
        for u in CustomUser.objects.all():
            print(f"  - {u.username}")
    except WorkItem.DoesNotExist:
        print(f"Work item with UUID '{work_item_uuid}' not found!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_transfer.py <username> [work_item_uuid]")
        print("Available users:")
        for u in CustomUser.objects.all():
            print(f"  - {u.username}")
        sys.exit(1)
    
    username = sys.argv[1]
    work_item_uuid = sys.argv[2] if len(sys.argv) > 2 else None
    
    test_transfer_permissions(username, work_item_uuid)