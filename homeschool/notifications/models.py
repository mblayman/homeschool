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
