import stripe
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse

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

        checkout_session = stripe.checkout.Session.create(
            customer_email=account.email,
            success_url=f"https://{site}{subscription_success}",
            cancel_url=f"https://{site}{stripe_cancel}",
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            # TODO: Need subscription_data.trial_end. Must be 48 hours in the future.
            client_reference_id=str(account.id),
        )
        return checkout_session["id"]


stripe_gateway = StripeGateway()
