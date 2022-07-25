from django.http import HttpRequest

from homeschool.students.models import Enrollment


def enrollment_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """Check if the user is authorized for an enrollment."""
    return Enrollment.objects.filter(
        grade_level__school_year__school__admin=request.user, pk=view_kwargs.get("pk")
    ).exists()
