from typing import Callable

import waffle
from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden


class DeniedMiddleware:
    """This middleware will deny all calls by default.

    A view must provide an authorizer that will return a boolean status
    to indicate whether to proceed or not.
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable,
        view_args: list,
        view_kwargs: dict,
    ):
        """Process the view by checking against an authorizer."""
        # If there's no authorizer, don't fail when the flag is off.
        if not (
            hasattr(view_func, "__denied_authorizer__")
            or waffle.flag_is_active(request, "denied-flag")
        ):
            return None

        if getattr(view_func, "__denied_exempt__", False):
            return None

        if not request.user.is_authenticated:
            return redirect_to_login(request.build_absolute_uri())

        if not hasattr(view_func, "__denied_authorizer__"):
            return HttpResponseForbidden()

        # __denied_authorizer__ is set by the various decorators.
        if not view_func.__denied_authorizer__(request, **view_kwargs):  # type: ignore
            return HttpResponseForbidden()
