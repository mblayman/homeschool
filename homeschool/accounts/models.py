from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords

from homeschool.users.models import User


class Account(models.Model):
    """A record to track the status of the account."""

    class AccountStatus(models.IntegerChoices):
        """The status of the account.

        State transitions:
        * TRIALING -> TRIAL_EXPIRED
        * TRIALING -> ACTIVE
        * ACTIVE -> PAST_DUE
        * ACTIVE -> CANCELED
        """

        EXEMPT = 1  # For special accounts that require no subscription
        BETA = 2  # For beta users
        TRIALING = 3
        ACTIVE = 4
        PAST_DUE = 5
        CANCELED = 6
        TRIAL_EXPIRED = 7

    ACTIVE_STATUSES = (
        AccountStatus.EXEMPT,
        AccountStatus.BETA,
        AccountStatus.TRIALING,
        AccountStatus.ACTIVE,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    status = models.IntegerField(
        choices=AccountStatus.choices, default=AccountStatus.TRIALING, db_index=True
    )

    history = HistoricalRecords()

    @property
    def email(self):
        """Get the account holder's email.

        This property is needed by dj-stripe.
        """
        return self.user.email


@receiver(post_save, sender=User)
def create_account(sender, instance, created, **kwargs):
    """A new user gets an associated account."""
    if created:
        Account.objects.create(user=instance)
