from django.contrib.messages import get_messages

from homeschool.referrals.models import Referral
from homeschool.test import TestCase


class TestReferralCreateView(TestCase):
    def test_post(self):
        user = self.make_user()
        data = {"email": "someone@somewhere.com"}

        with self.login(user):
            response = self.post("referrals:create", data=data)

        assert response.status_code == 302
        assert response["Location"] == self.reverse("settings:dashboard")
        message = list(get_messages(response.wsgi_request))[0]
        assert str(message) == "We will message your friend shortly."
        assert Referral.objects.filter(referring_user=user).count() == 1

    def test_bad_email(self):
        """A bad email address message is shown to the user."""
        user = self.make_user()
        data = {"email": "bogus"}

        with self.login(user):
            response = self.post("referrals:create", data=data)

        assert response.status_code == 302
        assert response["Location"] == self.reverse("settings:dashboard")
        message = list(get_messages(response.wsgi_request))[0]
        assert str(message) == "'bogus' is an invalid email address."

    def test_no_email(self):
        """A missing email display an appropriate message."""
        user = self.make_user()
        data: dict = {}

        with self.login(user):
            response = self.post("referrals:create", data=data)

        message = list(get_messages(response.wsgi_request))[0]
        assert str(message) == "'missing email' is an invalid email address."
