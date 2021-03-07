import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from djstripe.models import Price

from .stripe_gateway import stripe_gateway


@login_required
def subscriptions_index(request):
    """Show the subscription plan options."""
    livemode = settings.STRIPE_LIVE_MODE
    context = {
        "monthly_price": Price.objects.get(
            nickname=settings.ACCOUNTS_MONTHLY_PRICE_NICKNAME, livemode=livemode
        ),
        "annual_price": Price.objects.get(
            nickname=settings.ACCOUNTS_ANNUAL_PRICE_NICKNAME, livemode=livemode
        ),
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, "accounts/subscriptions_index.html", context)


@login_required
@require_POST
def create_checkout_session(request):
    """Create a checkout session for Stripe."""
    data = json.loads(request.body)
    price_id = data.get("price_id")

    if not Price.objects.filter(
        id=price_id, nickname__in=settings.ACCOUNTS_PRICE_NICKNAMES
    ).exists():
        messages.add_message(
            request,
            messages.ERROR,
            "That plan price is not available. Please contact support for help.",
        )
        return HttpResponseRedirect(reverse("subscriptions:index"))

    session_id = stripe_gateway.create_checkout_session(price_id, request.account)
    return JsonResponse({"session_id": session_id})


class SuccessView(LoginRequiredMixin, TemplateView):
    """The landing page after the user signs up for School Desk"""

    template_name = "accounts/subscriptions_success.html"


class StripeCancelView(LoginRequiredMixin, TemplateView):
    """The return page when a user cancels the request to create a subscription"""

    template_name = "accounts/subscriptions_stripe_cancel.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["support_email"] = settings.SUPPORT_EMAIL
        return context


@login_required
@require_POST
def create_billing_portal_session(request):
    """Create a billing portal session for a customer."""
    portal_url = stripe_gateway.create_billing_portal_session(request.account)
    return JsonResponse({"url": portal_url})
