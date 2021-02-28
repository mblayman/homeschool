import datetime

import stripe
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils import timezone

stripe.api_key = (
    settings.STRIPE_LIVE_SECRET_KEY
    if settings.STRIPE_LIVE_MODE
    else settings.STRIPE_TEST_SECRET_KEY
)


class StripeGateway:
    """A gateway to interact with the APIs required with Stripe."""

    def create_checkout_session(self, price_id, account):
        """Create a checkout session based on the subscription price."""
        site = Site.objects.get_current()
        subscription_success = reverse("subscriptions:success")
        stripe_cancel = reverse("subscriptions:stripe_cancel")

        session_parameters = {
            "customer_email": account.email,
            "success_url": f"https://{site}{subscription_success}",
            "cancel_url": f"https://{site}{stripe_cancel}",
            "payment_method_types": ["card"],
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "client_reference_id": str(account.id),
        }

        if self._is_trial_eligible(account):
            # Be generous and include an extra day.
            # This also makes Stripe display nicer so if someone signs up
            # on the same day with a credit card, it will show the full number
            # of days on the trial.
            trial_end = account.trial_end + datetime.timedelta(days=1)
            session_parameters["subscription_data"] = {
                # Stripe expects a Unix timestamp in whole seconds.
                "trial_end": int(trial_end.timestamp())
            }

        checkout_session = stripe.checkout.Session.create(**session_parameters)
        return checkout_session["id"]

    def _is_trial_eligible(self, account):
        """Check if the account is eligible for Stripe's trial data.

        The trial must end at least 48 hours in the future. See:
        https://stripe.com/docs/api/checkout/sessions/create#create_checkout_session-subscription_data-trial_end
        """
        cutoff = timezone.now() + datetime.timedelta(days=2)
        return account.trial_end > cutoff


stripe_gateway = StripeGateway()
