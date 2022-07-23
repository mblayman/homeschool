from typing import Callable

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
        if not hasattr(view_func, "__denied_authorizer__"):
            return HttpResponseForbidden()

        # __denied_authorizer__ is set by the various decorators.
        if not view_func.__denied_authorizer__(request, **view_kwargs):  # type: ignore
            return HttpResponseForbidden()
