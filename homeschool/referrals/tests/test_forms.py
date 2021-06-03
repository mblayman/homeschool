from homeschool.referrals.forms import ReferralForm
from homeschool.referrals.models import Referral
from homeschool.test import TestCase


class TestReferralForm(TestCase):
    def test_creates_referral(self):
        """The form creates a referral."""
        user = self.make_user()
        data = {"referring_user": str(user.id), "email": "someone@test.com"}
        form = ReferralForm(data=data)
        form.is_valid()

        form.save()

        assert Referral.objects.filter(referring_user=user).count() == 1
