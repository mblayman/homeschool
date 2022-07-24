import json

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from homeschool.denied.authorizers import any_authorized, staff_authorized
from homeschool.denied.decorators import authorize

from .models import Account
from .stripe_gateway import stripe_gateway


@authorize(staff_authorized)
def customers_dashboard(request):
    """Display info about current customers."""
    context = {
        "accounts": Account.objects.filter(
            status=Account.AccountStatus.ACTIVE
        ).select_related("user")
    }
    return render(request, "accounts/customers_dashboard.html", context)


@authorize(staff_authorized)
def customer_detail(request, id):
    """Display info about a customer."""
    context = {"account": Account.objects.select_related("user").get(id=id)}
    return render(request, "accounts/customer_detail.html", context)


@authorize(any_authorized)
def subscriptions_index(request):
    """Show the subscription plan options."""
    context = {
        "monthly_price": stripe_gateway.get_monthly_price(),
        "annual_price": stripe_gateway.get_annual_price(),
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, "accounts/subscriptions_index.html", context)


@require_POST
@authorize(any_authorized)
def create_checkout_session(request):
    """Create a checkout session for Stripe."""
    data = json.loads(request.body)
    price_id = data.get("price_id")

    if not stripe_gateway.has_price(price_id):
        messages.add_message(
            request,
            messages.ERROR,
            "That plan price is not available. Please contact support for help.",
        )
        return HttpResponseRedirect(reverse("subscriptions:index"))

    session_id = stripe_gateway.create_checkout_session(price_id, request.account)
    return JsonResponse({"session_id": session_id})


@authorize(any_authorized)
def success(request):
    """The landing page after the user signs up for School Desk"""
    return render(request, "accounts/subscriptions_success.html", {})


@authorize(any_authorized)
def stripe_cancel(request):
    """The return page when a user cancels the request to create a subscription"""
    context = {"support_email": settings.SUPPORT_EMAIL}
    return render(request, "accounts/subscriptions_stripe_cancel.html", context)


@require_POST
@authorize(any_authorized)
def create_billing_portal_session(request):
    """Create a billing portal session for a customer."""
    portal_url = stripe_gateway.create_billing_portal_session(request.account)
    return JsonResponse({"url": portal_url})
