import stripe
from django.conf import settings
from django.contrib.sites.models import Site

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
        checkout_session = stripe.checkout.Session.create(
            customer_email=account.email,
            # TODO: This URL needs to point to the appropriate spot.
            success_url=f"https://{site}?session_id={{CHECKOUT_SESSION_ID}}",
            # TODO: This URL needs to point to the appropriate spot.
            cancel_url=f"https://{site}",
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            # TODO: Need subscription_data.trial_end. Must be 48 hours in the future.
            client_reference_id=str(account.id),
        )
        return checkout_session["id"]


stripe_gateway = StripeGateway()
