import datetime

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from djstripe import webhooks
from simple_history.models import HistoricalRecords

from homeschool.users.models import User

from . import constants


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

    PRE_PLAN_STATUSES = (AccountStatus.TRIALING, AccountStatus.TRIAL_EXPIRED)
    END_STATUSES = (AccountStatus.CANCELED, AccountStatus.TRIAL_EXPIRED)

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

    @property
    def trial_end(self):
        """Calculate the account's trial end date."""
        return self.user.date_joined + datetime.timedelta(days=constants.TRIAL_DAYS)


@receiver(post_save, sender=User)
def create_account(sender, instance, created, **kwargs):
    """A new user gets an associated account."""
    if created:
        Account.objects.create(user=instance)


@webhooks.handler("checkout.session.completed")
def handle_checkout_session_completed(event, **kwargs):
    """Transition the account to an active state.

    This event occurs after a user provides their checkout payment information.
    """
    event_data = event.data["object"]
    # The Stripe gateway sets the account ID in the client reference ID field.
    account_id = int(event_data["client_reference_id"])
    Account.objects.filter(id=account_id).update(status=Account.AccountStatus.ACTIVE)
