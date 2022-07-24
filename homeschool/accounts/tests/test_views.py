from unittest import mock

from django.conf import settings
from django.contrib.messages import get_messages

from homeschool.accounts.tests.factories import AccountFactory, PriceFactory
from homeschool.test import TestCase
from homeschool.users.tests.factories import UserFactory


class TestCustomersDashboard(TestCase):
    def test_ok(self):
        user = UserFactory(is_staff=True)

        with self.login(user):
            self.get_check_200("office:accounts:customers_dashboard")


class TestCustomerDetail(TestCase):
    def test_ok(self):
        user = UserFactory(is_staff=True)
        account = AccountFactory()

        with self.login(user):
            self.get_check_200("office:accounts:customer_detail", account.id)


class TestSubscriptionsView(TestCase):
    def test_get(self):
        user = self.make_user()
        # The filter needs to consider livemode when getting prices.
        PriceFactory(nickname=settings.ACCOUNTS_MONTHLY_PRICE_NICKNAME)
        PriceFactory(nickname=settings.ACCOUNTS_MONTHLY_PRICE_NICKNAME, livemode=True)
        PriceFactory(nickname=settings.ACCOUNTS_ANNUAL_PRICE_NICKNAME)
        PriceFactory(nickname=settings.ACCOUNTS_ANNUAL_PRICE_NICKNAME, livemode=True)

        with self.login(user):
            self.get_check_200("subscriptions:index")

        assert self.get_context("monthly_price") is not None
        assert self.get_context("annual_price") is not None
        assert (
            self.get_context("stripe_publishable_key")
            == settings.STRIPE_PUBLISHABLE_KEY
        )


class TestCreateCheckoutSession(TestCase):
    @mock.patch("homeschool.accounts.views.stripe_gateway", autospec=True)
    def test_ok(self, mock_stripe_gateway):
        """The view gets a session from the gateway."""
        price = PriceFactory(nickname=settings.ACCOUNTS_MONTHLY_PRICE_NICKNAME)
        mock_stripe_gateway.create_checkout_session.return_value = "session_fake_id"
        user = self.make_user()
        data = {"price_id": price.id}

        with self.login(user):
            response = self.post(
                "subscriptions:create_checkout_session",
                data=data,
                extra={"content_type": "application/json"},
            )

        assert response.status_code == 200
        assert response.json()["session_id"] == "session_fake_id"

    def test_invalid_price(self):
        """If the price doesn't match an accepted active price, redirect with error."""
        user = self.make_user()
        PriceFactory(nickname=settings.ACCOUNTS_MONTHLY_PRICE_NICKNAME)
        data = {"price_id": "price_fake_id"}

        with self.login(user):
            response = self.post(
                "subscriptions:create_checkout_session",
                data=data,
                extra={"content_type": "application/json"},
            )

        assert response.status_code == 302
        message = list(get_messages(response.wsgi_request))[0]
        assert (
            str(message)
            == "That plan price is not available. Please contact support for help."
        )


class TestSuccessView(TestCase):
    def test_get(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("subscriptions:success")


class TestStripeCancelView(TestCase):
    def test_get(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("subscriptions:stripe_cancel")

        assert self.get_context("support_email") == settings.SUPPORT_EMAIL


@mock.patch("homeschool.accounts.views.stripe_gateway", autospec=True)
class TestCreateBillingPortalSession(TestCase):
    def test_ok(self, mock_stripe_gateway):
        """The view gets a session URL from the gateway."""
        mock_stripe_gateway.create_billing_portal_session.return_value = "/portal"
        user = self.make_user()

        with self.login(user):
            response = self.post(
                "subscriptions:create_billing_portal_session",
                extra={"content_type": "application/json"},
            )

        assert response.status_code == 200
        assert response.json()["url"] == "/portal"
