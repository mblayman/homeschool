from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import ProfileForm


@login_required
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
    return render(request, "users/settings_dashboard.html", {"form": form})
