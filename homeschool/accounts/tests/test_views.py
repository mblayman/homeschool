from unittest import mock

from django.conf import settings
from django.contrib.messages import get_messages

from homeschool.accounts.tests.factories import PriceFactory
from homeschool.test import TestCase


class TestSubscriptionsView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("subscriptions:index")

    def test_get(self):
        user = self.make_user()
        PriceFactory(nickname=settings.ACCOUNTS_MONTHLY_PRICE_NICKNAME)
        PriceFactory(nickname=settings.ACCOUNTS_ANNUAL_PRICE_NICKNAME)

        with self.login(user):
            self.get_check_200("subscriptions:index")

        assert self.get_context("monthly_price") is not None
        assert self.get_context("annual_price") is not None
        assert (
            self.get_context("stripe_publishable_key")
            == settings.STRIPE_PUBLISHABLE_KEY
        )


@mock.patch("homeschool.accounts.views.stripe_gateway", autospec=True)
class TestCreateCheckoutSession(TestCase):
    def test_unauthenticated_access(self, mock_stripe_gateway):
        self.assertLoginRequired("subscriptions:create_checkout_session")

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

    def test_invalid_price(self, mock_stripe_gateway):
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
        assert not mock_stripe_gateway.create_checkout_session.called
