import datetime
from unittest import mock

from django.utils import timezone

from homeschool.accounts import constants
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
        assert "subscription_data" in kwargs

    def test_no_trial_in_stripe_limits(self, mock_stripe):
        """A trial is not added to the session within Stripe's limit.

        Stripe does not permit a trial unless there are at least 48 hours from now.
        """
        too_close_date = timezone.now() - datetime.timedelta(
            days=constants.TRIAL_DAYS - 1  # Set the user 24 hours from trial ending.
        )
        account = AccountFactory(user__date_joined=too_close_date)
        gateway = StripeGateway()

        gateway.create_checkout_session("price_fake_id", account)

        kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert "subscription_data" not in kwargs
