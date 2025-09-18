#!/usr/bin/env python
import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Add the project root to the Python path
sys.path.append('/workspaces/MetaTasks')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediap.settings')
django.setup()

from services.cflows.models import WorkItem

def update_work_item_timestamps():
    # Get all work items that don't have current_step_entered_at set
    work_items = WorkItem.objects.filter(current_step_entered_at__isnull=True)
    print(f"Found {work_items.count()} work items without step entry timestamp")

    # Update them with realistic timestamps
    updated_count = 0
    for work_item in work_items:
        # Set to a few days ago to see the duration feature
        days_back = 2  # Default to 2 days ago
        
        # Add some variance based on work item ID for testing
        if work_item.id % 3 == 0:
            days_back = 5  # Some items 5 days old
        elif work_item.id % 2 == 0:
            days_back = 1  # Some items 1 day old
        
        work_item.current_step_entered_at = timezone.now() - timedelta(days=days_back)
        work_item.save()
        updated_count += 1
        print(f"Updated work item {work_item.id}: {work_item.title} - {days_back} days on current step")

    print(f"\nUpdated {updated_count} work items with step entry timestamps")

if __name__ == "__main__":
    update_work_item_timestamps()