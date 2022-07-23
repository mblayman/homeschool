from django.http import HttpRequest


def any_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """An authorizer that permits any access."""
    return True
