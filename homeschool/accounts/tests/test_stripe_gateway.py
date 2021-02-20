from unittest import mock

from homeschool.accounts.stripe_gateway import StripeGateway
from homeschool.accounts.tests.factories import AccountFactory
from homeschool.test import TestCase


@mock.patch("homeschool.accounts.stripe_gateway.stripe")
class TestStripeGateway(TestCase):
    def test_creates_session(self, mock_stripe):
        """The gateway creates a checkout session for the price."""
        account = AccountFactory()
        mock_stripe.checkout.Session.create.return_value = {"id": "fake_session_id"}
        gateway = StripeGateway()

        session_id = gateway.create_checkout_session("price_fake_id", account)

        assert session_id == "fake_session_id"
        kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert kwargs["customer_email"] == account.email
        assert kwargs["client_reference_id"] == str(account.id)
