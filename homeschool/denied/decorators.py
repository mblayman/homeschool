from functools import wraps
from typing import Callable

from .authorizers import any_authorized


def allow(view_func: Callable) -> Callable:
    """Allow a view without any authorization checking."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapper.__denied_authorizer__ = any_authorized  # type: ignore
    return wrapper
