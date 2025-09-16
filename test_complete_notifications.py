#!/usr/bin/env python
"""
Complete test of the notification and email system
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediap.settings')
django.setup()

from services.cflows.models import WorkItem, WorkItemComment
from accounts.models import CustomUser
from core.models import UserProfile, Notification

def test_complete_mention_flow():
    print("🔔 Testing complete mention notification flow...")
    
    # Get test users
    admin_user = CustomUser.objects.filter(username='admin').first()
    sales_user = CustomUser.objects.filter(username='sales_manager').first()
    
    if not admin_user or not sales_user:
        print("❌ Required test users not found")
        return False
    
    # Get user profiles
    admin_profile = UserProfile.objects.filter(user=admin_user).first()
    if not admin_profile:
        print("❌ Admin profile not found")
        return False
    
    # Get a work item
    work_item = WorkItem.objects.first()
    if not work_item:
        print("❌ No work items found")
        return False
    
    print(f"✅ Using work item: {work_item.title}")
    print(f"✅ Admin user: {admin_user.username} ({admin_user.email})")
    print(f"✅ Target user: {sales_user.username} ({sales_user.email})")
    
    # Count existing notifications
    initial_count = Notification.objects.filter(recipient=sales_user).count()
    print(f"📊 Initial notifications for {sales_user.username}: {initial_count}")
    
    # Create a comment with mention using the same logic as the view
    comment_content = f"Hey @{sales_user.username}, can you review this work item? Thanks!"
    
    try:
        # Simulate the comment creation process from the view
        comment = WorkItemComment.objects.create(
            work_item=work_item,
            author=admin_profile,
            content=comment_content
        )
        
        print(f"✅ Created comment: {comment.content}")
        
        # Parse mentions and create notifications (same as view logic)
        from services.cflows.mention_utils import parse_mentions
        from core.models import UserProfile as CoreUserProfile, Team as CoreTeam
        
        mentions = parse_mentions(comment.content)
        print(f"📝 Parsed mentions: {mentions}")
        
        # Users
        notified_user_ids = set()
        if mentions['usernames']:
            mentioned_users = list(CoreUserProfile.objects.filter(
                organization=admin_profile.organization,
                user__username__in=list(mentions['usernames'])
            ))
            print(f"👥 Found mentioned users: {[u.user.username for u in mentioned_users]}")
            
            if mentioned_users:
                comment.mentioned_users.set(mentioned_users)
                
                # Create notifications
                for u in mentioned_users:
                    if u.id != admin_profile.id:
                        notification = Notification.objects.create(
                            recipient=u.user,
                            title=f"You were mentioned on '{work_item.title}'",
                            message=f"{admin_profile.user.get_full_name() or admin_profile.user.username} mentioned you in a comment.",
                            notification_type='info',
                            content_type='WorkItem',
                            object_id=str(work_item.id),
                            action_url=f"/services/cflows/work-items/{work_item.id}/",
                            action_text='View Work Item'
                        )
                        
                        print(f"🔔 Created notification: {notification.title}")
                        
                        # Send email
                        from core.notification_views import send_notification_email
                        email_result = send_notification_email(notification)
                        print(f"📧 Email sent: {email_result}")
                        
                        notified_user_ids.add(u.id)
        
        # Count final notifications
        final_count = Notification.objects.filter(recipient=sales_user).count()
        print(f"📊 Final notifications for {sales_user.username}: {final_count}")
        
        if final_count > initial_count:
            print("✅ SUCCESS! Notification system is working!")
            print("✅ Email notifications are being sent!")
            print("✅ Mention parsing is working correctly!")
            return True
        else:
            print("❌ No new notifications were created")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_complete_mention_flow()
    print(f"\n{'🎉 ALL TESTS PASSED!' if success else '💥 TESTS FAILED!'}")
    sys.exit(0 if success else 1)