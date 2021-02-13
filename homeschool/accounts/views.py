from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def subscriptions_index(request):
    return render(request, "accounts/subscriptions_index.html", {})
