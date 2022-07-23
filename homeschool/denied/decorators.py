from functools import wraps
from typing import Callable

from .authorizers import any_authorized


# TODO: How do I exempt unauthenticated views from this check?
# Maybe in `allow`, I can add __denied_authentication_required__
def allow(view_func: Callable) -> Callable:
    """Allow a view without any authorization checking."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapper.__denied_authorizer__ = any_authorized  # type: ignore
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
