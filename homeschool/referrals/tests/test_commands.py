from io import StringIO
from unittest import mock

from homeschool.referrals.management.commands.send_referrals import Command
from homeschool.referrals.models import Referral
from homeschool.referrals.tests.factories import ReferralFactory
from homeschool.test import TestCase


class TestSendReferrals(TestCase):
    @mock.patch(
        "homeschool.referrals.management.commands.send_referrals.send_mail",
        autospec=True,
    )
    def test_sends_referrals(self, send_mail):
        """The commands sends pending referrals."""
        stdout = StringIO()
        ReferralFactory(status=Referral.Status.PENDING)
        ReferralFactory(status=Referral.Status.PENDING)
        command = Command(stdout=stdout)

        command.handle()

        assert Referral.objects.filter(status=Referral.Status.SENT).count() == 2
        assert send_mail.call_count == 2
