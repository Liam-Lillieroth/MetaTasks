"""
Email notification tasks using Celery
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, retry_backoff=300, max_retries=3)
def send_mention_notification_email(self, notification_id):
    """
    Send email notification for mentions in comments
    """
    try:
        from core.models import Notification
        notification = Notification.objects.select_related('recipient').get(id=notification_id)
        
        # Check if user has email notifications enabled
        try:
            user_profile = notification.recipient.mediap_profile
            if not user_profile.email_notifications:
                logger.info(f"Email notifications disabled for user {notification.recipient.username}")
                return "Email notifications disabled for user"
        except:
            # Default to sending if no profile exists
            pass
        
        # Check if email already sent
        if notification.email_sent:
            logger.info(f"Email already sent for notification {notification_id}")
            return "Email already sent"
        
        # Prepare email content
        context = {
            'notification': notification,
            'recipient': notification.recipient,
            'action_url': f"{settings.SITE_URL or 'http://localhost:8000'}{notification.action_url}" if notification.action_url else None,
        }
        
        # Render email templates
        html_content = render_to_string('emails/mention_notification.html', context)
        text_content = strip_tags(html_content)
        
        # Send email
        success = send_mail(
            subject=f"MetaTask: {notification.title}",
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            html_message=html_content,
            fail_silently=False
        )
        
        if success:
            # Mark email as sent
            notification.email_sent = True
            notification.email_sent_at = timezone.now()
            notification.save(update_fields=['email_sent', 'email_sent_at'])
            
            logger.info(f"Email sent successfully for notification {notification_id}")
            return "Email sent successfully"
        else:
            logger.error(f"Failed to send email for notification {notification_id}")
            raise Exception("Email sending failed")
            
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return "Notification not found"
    except Exception as exc:
        logger.error(f"Error sending email for notification {notification_id}: {exc}")
        # Retry the task
        raise self.retry(exc=exc)


@shared_task
def send_daily_digest_emails():
    """
    Send daily digest emails to users with pending notifications
    """
    try:
        from core.models import Notification, UserProfile
        from django.db import models
        from datetime import timedelta
        
        # Get users who want daily digests and have unread notifications
        yesterday = timezone.now() - timedelta(days=1)
        
        # Find users with unread notifications from the last 24 hours
        users_with_notifications = User.objects.filter(
            notifications__is_read=False,
            notifications__created_at__gte=yesterday
        ).distinct()
        
        for user in users_with_notifications:
            try:
                user_profile = user.mediap_profile
                if user_profile.digest_frequency != 'daily' or not user_profile.email_notifications:
                    continue
                    
                # Get unread notifications for this user
                unread_notifications = user.notifications.filter(
                    is_read=False,
                    created_at__gte=yesterday
                ).order_by('-created_at')
                
                if not unread_notifications.exists():
                    continue
                
                # Prepare email content
                context = {
                    'user': user,
                    'notifications': unread_notifications,
                    'site_url': settings.SITE_URL or 'http://localhost:8000',
                    'organization': user_profile.organization,
                }
                
                # Render email templates
                html_content = render_to_string('emails/daily_digest.html', context)
                text_content = strip_tags(html_content)
                
                # Send email
                send_mail(
                    subject=f"MetaTask Daily Digest - {unread_notifications.count()} new notifications",
                    message=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_content,
                    fail_silently=False
                )
                
                logger.info(f"Daily digest sent to {user.email}")
                
            except Exception as e:
                logger.error(f"Error sending daily digest to {user.email}: {e}")
                continue
                
    except Exception as exc:
        logger.error(f"Error in daily digest task: {exc}")


@shared_task
def send_work_item_assignment_email(work_item_id, assigned_user_id):
    """
    Send email notification when a work item is assigned to a user
    """
    try:
        from services.cflows.models import WorkItem
        from django.contrib.auth.models import User
        
        work_item = WorkItem.objects.select_related('workflow', 'current_step').get(id=work_item_id)
        assigned_user = User.objects.get(id=assigned_user_id)
        
        # Check if user has email notifications enabled
        try:
            user_profile = assigned_user.mediap_profile
            if not user_profile.email_notifications:
                return "Email notifications disabled for user"
        except:
            pass
        
        # Prepare email content
        context = {
            'work_item': work_item,
            'assigned_user': assigned_user,
            'site_url': settings.SITE_URL or 'http://localhost:8000',
        }
        
        # Render email templates
        html_content = render_to_string('emails/work_item_assignment.html', context)
        text_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=f"MetaTask: New work item assigned - {work_item.title}",
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[assigned_user.email],
            html_message=html_content,
            fail_silently=False
        )
        
        logger.info(f"Work item assignment email sent to {assigned_user.email}")
        return "Email sent successfully"
        
    except Exception as exc:
        logger.error(f"Error sending work item assignment email: {exc}")
        raise


@shared_task
def cleanup_old_notifications():
    """
    Clean up old notifications based on their expires_at date
    """
    try:
        from core.models import Notification
        
        # Delete expired notifications
        expired_count = Notification.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        
        # Delete read notifications older than 30 days
        old_read_count = Notification.objects.filter(
            is_read=True,
            read_at__lt=timezone.now() - timedelta(days=30)
        ).delete()[0]
        
        logger.info(f"Cleaned up {expired_count} expired and {old_read_count} old read notifications")
        return f"Cleaned up {expired_count + old_read_count} notifications"
        
    except Exception as exc:
        logger.error(f"Error cleaning up notifications: {exc}")
        raise