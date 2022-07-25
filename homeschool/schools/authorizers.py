from django.http import HttpRequest

from homeschool.schools.models import SchoolYear


def school_year_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """Check if the user is authorized for a school year."""
    return SchoolYear.objects.filter(
        school__admin=request.user, pk=view_kwargs.get("pk")
    ).exists()
