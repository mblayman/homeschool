import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .stripe_gateway import stripe_gateway


@login_required
def subscriptions_index(request):
    """Show the subscription plan options."""
    return render(request, "accounts/subscriptions_index.html", {})


@login_required
@require_POST
def create_checkout_session(request):
    """Create a checkout session for Stripe."""
    data = json.loads(request.body)
    # TODO: Validate that the price is real.
    session_id = stripe_gateway.create_checkout_session(data.get("price_id"))
    return JsonResponse({"session_id": session_id})
