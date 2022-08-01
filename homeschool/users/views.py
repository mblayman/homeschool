from denied.authorizers import any_authorized
from denied.decorators import authorize
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from homeschool.referrals.forms import ReferralForm

from .forms import ProfileForm


@authorize(any_authorized)
def settings_dashboard(request):
    """A dashboard of all the user's settings."""
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.add_message(
                request, messages.SUCCESS, "Your settings updated successfully."
            )
            return redirect(reverse("settings:dashboard"))
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(
        request,
        "users/settings_dashboard.html",
        {"form": form, "nav_link": "settings", "referral_form": ReferralForm()},
    )
