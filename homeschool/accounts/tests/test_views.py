from unittest import mock

from homeschool.test import TestCase


class TestSubscriptionsView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("subscriptions:index")

    def test_get(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("subscriptions:index")


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
