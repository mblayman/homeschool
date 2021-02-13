from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from homeschool.accounts.middleware import AccountGateMiddleware
from homeschool.accounts.models import Account
from homeschool.test import TestCase, get_response


class TestAccountGateMiddleware(TestCase):
    rf = RequestFactory()

    def test_request_has_account(self):
        """The user's account is added to the request."""
        request = self.rf.get("/")
        request.user = self.make_user()
        middleware = AccountGateMiddleware(get_response)

        middleware(request)

        assert request.account == Account.objects.filter(user=request.user).first()

    def test_anonymous_user(self):
        """An anonymous user has no account."""
        request = self.rf.get("/")
        request.user = AnonymousUser()
        middleware = AccountGateMiddleware(get_response)

        middleware(request)

        assert request.account is None

    def test_inactive_redirect(self):
        """An inactive account redirect to the subscriptions page."""
        request = self.rf.get("/")
        request.user = self.make_user()
        expired = Account.AccountStatus.TRIAL_EXPIRED
        Account.objects.filter(user=request.user).update(status=expired)
        middleware = AccountGateMiddleware(get_response)

        response = middleware(request)

        assert response.status_code == 302
        assert response["Location"] == self.reverse("subscriptions:index")
