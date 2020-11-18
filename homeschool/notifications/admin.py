import requests
from django.contrib import admin, messages
from django.contrib.sites.shortcuts import get_current_site

from homeschool.accounts.models import Account
from homeschool.users.models import User

from .models import Announcement, Notification


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    actions = ["announce"]
    list_display = ("url", "status")

    def announce(self, request, queryset):
        """Announce the announcement by creating user notifications."""
        if len(queryset) != 1:
            messages.add_message(request, messages.ERROR, "Select one.")
            return

        announcement = queryset[0]
        if announcement.status != Announcement.AnnouncementStatus.PENDING:
            messages.add_message(
                request, messages.ERROR, "That announcement is already announced."
            )
            return

        if not self._check_url(request, announcement):
            messages.add_message(
                request, messages.ERROR, "The announcement URL was a non-200 response."
            )
            return

        self._create_notifications(announcement)

        announcement.status = Announcement.AnnouncementStatus.ANNOUNCED
        announcement.save()

    def _check_url(self, request, announcement):
        """Check that the URL is valid."""
        scheme = "https://" if request.is_secure() else "http://"
        site = get_current_site(request)
        url = f"{scheme}{site}{announcement.url}"
        response = requests.get(url, timeout=5)
        return response.status_code == 200

    def _create_notifications(self, announcement):
        """Create all the user notifications."""
        users_wanting_announcements = set(
            User.objects.filter(profile__wants_announcements=True).values_list(
                "id", flat=True
            )
        )
        canceled = Account.AccountStatus.CANCELED
        canceled_users = set(
            Account.objects.filter(status=canceled).values_list("user_id", flat=True)
        )
        users_to_notify = users_wanting_announcements - canceled_users
        notifications = [
            Notification(announcement=announcement, user_id=user_id)
            for user_id in users_to_notify
        ]
        Notification.objects.bulk_create(notifications)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "announcement", "status")
