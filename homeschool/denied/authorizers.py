from django.http import HttpRequest


def any_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """An authorizer that permits any access."""
    return True


def staff_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """An authorizer for staff users"""
    return request.user.is_authenticated and request.user.is_staff
