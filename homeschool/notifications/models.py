from django.conf import settings
from django.db import models


class Announcement(models.Model):
    """For making product announcements"""

    class AnnouncementStatus(models.IntegerChoices):
        PENDING = 1
        ANNOUNCED = 2

    status = models.IntegerField(
        choices=AnnouncementStatus.choices, default=AnnouncementStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.url}"


class Notification(models.Model):
    """For tracking if a user has seen an announcement"""

    class NotificationStatus(models.IntegerChoices):
        UNREAD = 1
        VIEWED = 2

    status = models.IntegerField(
        choices=NotificationStatus.choices, default=NotificationStatus.UNREAD
    )
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)

    def __str__(self):
        return f"Notification for {self.user} for {self.announcement}"
