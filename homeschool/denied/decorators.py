from __future__ import annotations

from functools import wraps
from typing import Callable, overload

from django.urls.resolvers import URLPattern


@overload
def allow(view_func: Callable) -> Callable:
    ...


@overload
def allow(view_func: tuple) -> tuple:
    ...


def allow(view_func: Callable | tuple) -> Callable | tuple:
    """Allow a view without any authorization checking."""

    # When used around `include`, view_func will not be a callable.
    # Recursively allow any view function in the included routes.
    if isinstance(view_func, tuple):
        urlconf_module, _, _ = view_func
        for url in urlconf_module.urlpatterns:
            if isinstance(url, URLPattern):
                url.callback.__denied_exempt__ = True
            else:
                allow((url.urlconf_module, None, None))
        return view_func

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # mypy is ignoring the isinstance check for some reason.
        return view_func(*args, **kwargs)  # type: ignore

    wrapper.__denied_exempt__ = True  # type: ignore
    return wrapper


def authorize(authorizer: Callable) -> Callable:
    """Add an authorizer to a view."""

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            return view_func(*args, **kwargs)

        wrapper.__denied_authorizer__ = authorizer  # type: ignore
        return wrapper

    return decorator
