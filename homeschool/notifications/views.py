from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from .models import Notification


@login_required
def send_whats_new(request):
    """Redirect the user to the notification announcement's URL.

    This has the side effect of cleaning out any unread notifications too.
    """
    unread_notifications = Notification.objects.filter(
        user=request.user, status=Notification.NotificationStatus.UNREAD
    )
    notification = (
        unread_notifications.order_by("created_at")
        .select_related("announcement")
        .last()
    )
    if notification:
        unread_notifications.update(status=Notification.NotificationStatus.VIEWED)
        return redirect(notification.announcement.url)
    return redirect(reverse("core:app"))
