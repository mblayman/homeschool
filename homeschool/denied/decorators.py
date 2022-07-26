from __future__ import annotations

from collections.abc import Iterable
from functools import wraps
from typing import Callable, overload

from django.urls.resolvers import URLPattern, URLResolver


@overload
def allow(view_func: Callable) -> Callable:
    ...  # pragma: no cover


@overload
def allow(view_func: list) -> list:
    ...  # pragma: no cover


@overload
def allow(view_func: tuple) -> tuple:
    ...  # pragma: no cover


def allow(view_func: Callable | list | tuple) -> Callable | list | tuple:
    """Allow a view without any authorization checking."""

    if isinstance(view_func, (list, tuple)):
        _allow_many(view_func)
        return view_func

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # mypy is ignoring the isinstance check for some reason.
        return view_func(*args, **kwargs)  # type: ignore

    wrapper.__denied_exempt__ = True  # type: ignore
    return wrapper


def _allow_many(view_func: list | tuple) -> None:
    """Allow many views.

    When used around `include`, view_func will not be a callable.
    Also, handle when a list of URLs is provided directly (e.g., `admin.site.urls`).
    Recursively allow any view function in the included routes.
    """
    urlpatterns: Iterable = []
    # Sniff out whether this is like the return of `include` or just a 3-tuple.
    if view_func and hasattr(view_func[0], "urlpatterns"):
        urlpatterns = view_func[0].urlpatterns
    else:
        urlpatterns = view_func[0]

    for url in urlpatterns:
        if isinstance(url, URLPattern):
            if hasattr(url.callback, "__self__"):
                # Attributes cannot be added to bound methods,
                # so add to the underlying function instead.
                url.callback.__func__.__denied_exempt__ = True
            else:
                url.callback.__denied_exempt__ = True
        elif isinstance(url, URLResolver):
            allow((url.urlconf_module, None, None))


def authorize(authorizer: Callable) -> Callable:
    """Add an authorizer to a view."""

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            return view_func(*args, **kwargs)

        wrapper.__denied_authorizer__ = authorizer  # type: ignore
        return wrapper

    return decorator
