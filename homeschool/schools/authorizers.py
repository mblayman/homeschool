from django.http import HttpRequest

from homeschool.schools.models import GradeLevel, SchoolBreak, SchoolYear


def grade_level_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """Check if the user is authorized for a grade level."""
    return GradeLevel.objects.filter(
        school_year__school__admin=request.user, pk=view_kwargs.get("pk")
    ).exists()


def school_break_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """Check if the user is authorized for a school break."""
    return SchoolBreak.objects.filter(
        school_year__school__admin=request.user, pk=view_kwargs.get("pk")
    ).exists()


def school_year_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """Check if the user is authorized for a school year."""
    return SchoolYear.objects.filter(
        school__admin=request.user, pk=view_kwargs.get("pk")
    ).exists()
