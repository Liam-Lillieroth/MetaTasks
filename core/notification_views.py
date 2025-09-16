"""
Notification views for displaying and managing user notifications
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from core.models import Notification
from core.decorators import require_organization_access
from core.user_management_views import get_user_profile


def send_notification_email(notification):
    """Send email notification to user"""
    if not notification.recipient.email:
        return False
    
    try:
        # Render email content
        context = {
            'notification': notification,
            'user': notification.recipient,
        }
        
        html_content = render_to_string('emails/notification.html', context)
        text_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=f'[MetaTasks] {notification.title}',
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            html_message=html_content,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email notification: {e}")
        return False


@login_required
def notification_center(request):
    """Display all notifications for the current user"""
    # Get filter parameters
    filter_type = request.GET.get('type', 'all')
    mark_all_read = request.GET.get('mark_read') == '1'
    
    # Mark all as read if requested
    if mark_all_read:
        request.user.notifications.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        messages.success(request, 'All notifications marked as read.')
        return redirect('core:notification_center')
    
    # Get notifications
    notifications = request.user.notifications.all()
    
    # Apply filters
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'mentions':
        notifications = notifications.filter(
            Q(title__icontains='mentioned') | Q(message__icontains='mentioned')
        )
    elif filter_type == 'assignments':
        notifications = notifications.filter(
            Q(title__icontains='assigned') | Q(message__icontains='assigned')
        )
    
    # Paginate
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Count stats
    unread_count = request.user.notifications.filter(is_read=False).count()
    total_count = request.user.notifications.count()
    
    context = {
        'notifications': page_obj,
        'filter_type': filter_type,
        'unread_count': unread_count,
        'total_count': total_count,
        'page_obj': page_obj,
    }
    
    return render(request, 'core/notification_center.html', context)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    
    if not notification.is_read:
        notification.mark_as_read()
    
    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'read': True})
    
    # Redirect for regular requests
    next_url = request.POST.get('next', '/notifications/')
    return redirect(next_url)


@login_required
def notification_api(request):
    """API endpoint for getting notifications (for dropdown/bell icon)"""
    # Get recent unread notifications
    notifications = request.user.notifications.filter(
        is_read=False
    ).order_by('-created_at')[:10]
    
    data = []
    for notification in notifications:
        data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'created_at': notification.created_at.isoformat(),
            'action_url': notification.action_url,
            'action_text': notification.action_text,
        })
    
    return JsonResponse({
        'notifications': data,
        'unread_count': request.user.notifications.filter(is_read=False).count(),
        'total_count': request.user.notifications.count(),
    })


@login_required
@require_POST
def delete_notification(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    
    notification.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Notification deleted.')
    return redirect('core:notification_center')


@login_required
def notification_preferences(request):
    """Manage notification preferences"""
    profile = get_user_profile(request)
    
    if request.method == 'POST':
        # Update preferences
        profile.email_notifications = request.POST.get('email_notifications') == 'on'
        profile.desktop_notifications = request.POST.get('desktop_notifications') == 'on'
        digest_frequency = request.POST.get('digest_frequency')
        if digest_frequency in ['daily', 'weekly', 'monthly', 'never']:
            profile.digest_frequency = digest_frequency
        
        profile.save()
        messages.success(request, 'Notification preferences updated.')
        return redirect('core:notification_preferences')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'core/notification_preferences.html', context)