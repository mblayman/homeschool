import datetime

from homeschool.accounts import constants
from homeschool.accounts.models import Account
from homeschool.accounts.tests.factories import AccountFactory
from homeschool.test import TestCase


class TestAccount(TestCase):
    def test_factory(self):
        account = AccountFactory()

        assert account.user is not None
        assert account.status == Account.AccountStatus.TRIALING

    def test_email(self):
        """The account proxies the account holder's email address."""
        account = AccountFactory()

        assert account.email == account.user.email

    def test_trial_end(self):
        """The account has a trial end date."""
        account = AccountFactory()

        assert account.trial_end == account.user.date_joined + datetime.timedelta(
            days=constants.TRIAL_DAYS
        )
