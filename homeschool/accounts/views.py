import json

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST
from djstripe.models import Price

from .models import Account
from .stripe_gateway import stripe_gateway


@staff_member_required
def customers_dashboard(request):
    """Display info about current customers."""
    context = {
        "accounts": Account.objects.filter(
            status=Account.AccountStatus.ACTIVE
        ).select_related("user")
    }
    return render(request, "accounts/customers_dashboard.html", context)


@staff_member_required
def customer_detail(request, id):
    """Display info about a customer."""
    context = {"account": Account.objects.select_related("user").get(id=id)}
    return render(request, "accounts/customer_detail.html", context)


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


@login_required
def success(request):
    """The landing page after the user signs up for School Desk"""
    return render(request, "accounts/subscriptions_success.html", {})


@login_required
def stripe_cancel(request):
    """The return page when a user cancels the request to create a subscription"""
    context = {"support_email": settings.SUPPORT_EMAIL}
    return render(request, "accounts/subscriptions_stripe_cancel.html", context)


@login_required
@require_POST
def create_billing_portal_session(request):
    """Create a billing portal session for a customer."""
    portal_url = stripe_gateway.create_billing_portal_session(request.account)
    return JsonResponse({"url": portal_url})
