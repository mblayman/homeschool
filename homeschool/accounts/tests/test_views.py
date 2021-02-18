from unittest import mock

from django.conf import settings
from djstripe.models import Price, Product

from homeschool.test import TestCase


class TestSubscriptionsView(TestCase):
    def setUp(self):
        product = Product.objects.create()
        Price.objects.create(
            nickname=settings.ACCOUNTS_MONTHLY_PRICE_NICKNAME,
            active=True,
            product=product,
            id="price_fake_monthly",
        )
        Price.objects.create(
            nickname=settings.ACCOUNTS_ANNUAL_PRICE_NICKNAME,
            active=True,
            product=product,
            id="price_fake_annual",
        )

    def test_unauthenticated_access(self):
        self.assertLoginRequired("subscriptions:index")

    def test_get(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("subscriptions:index")

        assert self.get_context("monthly_price") is not None
        assert self.get_context("annual_price") is not None
        assert (
            self.get_context("stripe_publishable_key")
            == settings.STRIPE_PUBLISHABLE_KEY
        )


class TestCreateCheckoutSession(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("subscriptions:create_checkout_session")

    @mock.patch("homeschool.accounts.views.stripe_gateway")
    def test_ok(self, mock_stripe_gateway):
        """The view gets a session from the gateway."""
        mock_stripe_gateway.create_checkout_session.return_value = "session_fake_id"
        user = self.make_user()
        data = {"price_id": "price_fake_id"}

        with self.login(user):
            response = self.post(
                "subscriptions:create_checkout_session",
                data=data,
                extra={"content_type": "application/json"},
            )

        assert response.status_code == 200
        assert response.json()["session_id"] == "session_fake_id"
