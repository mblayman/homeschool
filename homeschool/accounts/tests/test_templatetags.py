import datetime

from django.test import RequestFactory
from django.utils import timezone

from homeschool.accounts import constants
from homeschool.accounts.models import Account
from homeschool.accounts.templatetags import accounts_tags
from homeschool.accounts.tests.factories import AccountFactory
from homeschool.test import TestCase


class TestTrialBanner(TestCase):
    rf = RequestFactory()

    def test_non_trialing(self):
        """Non-TRIALING accounts do not see the banner."""
        account = AccountFactory(status=Account.AccountStatus.ACTIVE)
        request = self.rf.get("/")
        request.account = account
        context = {"request": request}

        context = accounts_tags.trial_banner(context)

        assert not context["display_banner"]

    def test_display_banner(self):
        """An old TRIALING account displays the trial banner."""
        old_trial_start = timezone.now() - datetime.timedelta(days=constants.TRIAL_DAYS)
        account = AccountFactory(
            status=Account.AccountStatus.TRIALING, user__date_joined=old_trial_start
        )
        request = self.rf.get("/")
        request.account = account
        context = {"request": request}

        context = accounts_tags.trial_banner(context)

        assert context["display_banner"]
