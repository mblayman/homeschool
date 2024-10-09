import datetime

from django.utils import timezone

from homeschool.accounts import constants
from homeschool.accounts.models import Account
from homeschool.accounts.tasks import expire_trials
from homeschool.accounts.tests.factories import AccountFactory
from homeschool.test import TestCase


class TestExpireTrials(TestCase):
    def test_expires_trials(self):
        """Old trials are marked as expired."""
        trialing = Account.AccountStatus.TRIALING
        account = AccountFactory(
            status=trialing,
            user__date_joined=timezone.now()
            - datetime.timedelta(days=constants.TRIAL_DAYS + 5),
        )

        expire_trials()

        account.refresh_from_db()
        assert account.status == Account.AccountStatus.TRIAL_EXPIRED

    def test_keep_active_trials(self):
        """Recent trials are not expired."""
        trialing = Account.AccountStatus.TRIALING
        account = AccountFactory(status=trialing, user__date_joined=timezone.now())

        expire_trials()

        account.refresh_from_db()
        assert account.status == Account.AccountStatus.TRIALING

    def test_other_statuses_not_expired(self):
        """Only TRIALING is marked as expired."""
        active = Account.AccountStatus.ACTIVE
        account = AccountFactory(
            status=active,
            user__date_joined=timezone.now()
            - datetime.timedelta(days=constants.TRIAL_DAYS + 5),
        )

        expire_trials()

        account.refresh_from_db()
        assert account.status == Account.AccountStatus.ACTIVE
