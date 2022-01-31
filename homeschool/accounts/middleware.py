import re

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Account


class AccountGateMiddleware:
    """Check that an account is in a valid status to permit access.

    Inactive accounts will be redirected to a plan selection page
    unless the URL is on an allowed list of routes.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.allow_list_patterns = [
            re.compile(rf"^{allowed}$") for allowed in settings.ACCOUNT_GATE_ALLOW_LIST
        ]

    def __call__(self, request):
        request.account = None
        if request.user.is_authenticated:
            request.account = Account.objects.filter(user=request.user).first()

            gate_url = reverse("subscriptions:index")
            if (
                request.account.status in Account.ACTIVE_STATUSES
                or request.path_info == gate_url
                or self.is_allowed(request.path_info)
            ):
                return self.get_response(request)

            return HttpResponseRedirect(gate_url)
        return self.get_response(request)

    def is_allowed(self, path):
        """Check if the request is allowed against the allow list."""
        return any(pattern.match(path) for pattern in self.allow_list_patterns)
