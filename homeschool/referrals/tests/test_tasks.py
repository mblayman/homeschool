from unittest import mock

from homeschool.referrals.models import Referral
from homeschool.referrals.tasks import send_referrals
from homeschool.referrals.tests.factories import ReferralFactory
from homeschool.test import TestCase


class TestSendReferrals(TestCase):
    @mock.patch("homeschool.referrals.tasks.send_mail", autospec=True)
    def test_sends_referrals(self, send_mail):
        """The commands sends pending referrals."""
        ReferralFactory(status=Referral.Status.PENDING)
        ReferralFactory(status=Referral.Status.PENDING)

        send_referrals()

        assert Referral.objects.filter(status=Referral.Status.SENT).count() == 2
        assert send_mail.call_count == 2
