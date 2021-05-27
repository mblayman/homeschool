from homeschool.referrals.tests.factories import ReferralFactory
from homeschool.test import TestCase


class TestReferral(TestCase):
    def test_factory(self):
        referral = ReferralFactory()

        assert referral.referring_user is not None
        assert referral.created_at is not None
        assert referral.status == referral.Status.PENDING
