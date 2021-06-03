from django.conf import settings
from django.db import models
from django.utils import timezone


class Referral(models.Model):
    """A referral allows customers to share School Desk with others"""

    class Status(models.IntegerChoices):
        PENDING = 1
        SENT = 2
        CONVERTED = 3

    referring_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referrals"
    )
    email = models.EmailField()
    created_at = models.DateField(default=timezone.localdate)
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)
