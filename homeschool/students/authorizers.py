from django.db.models import Q
from django.http import HttpRequest

from homeschool.students.models import Enrollment, Student


def enrollment_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """Check if the user is authorized for an enrollment."""
    return Enrollment.objects.filter(
        Q(grade_level__school_year__school__admin=request.user)
        | Q(student__school__admin=request.user),
        pk=view_kwargs.get("pk"),
    ).exists()


def student_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """Check if the user is authorized for a student."""
    return Student.objects.filter(
        school__admin=request.user, pk=view_kwargs.get("pk")
    ).exists()
