from django.http import HttpRequest

from homeschool.courses.models import Course, CourseResource, CourseTask
from homeschool.schools.models import GradeLevel


def course_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """Check if the user is authorized for a course."""
    grade_levels = GradeLevel.objects.filter(school_year__school__admin=request.user)
    return Course.objects.filter(
        grade_levels__in=grade_levels, pk=view_kwargs.get("pk")
    ).exists()


def task_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """Check if the user is authorized for a course task."""
    grade_levels = GradeLevel.objects.filter(school_year__school__admin=request.user)
    return CourseTask.objects.filter(
        course__grade_levels__in=grade_levels, pk=view_kwargs.get("pk")
    ).exists()


def resource_authorized(request: HttpRequest, **view_kwargs: dict) -> bool:
    """Check if the user is authorized for a course resource."""
    grade_levels = GradeLevel.objects.filter(school_year__school__admin=request.user)
    return CourseResource.objects.filter(
        course__grade_levels__in=grade_levels, pk=view_kwargs.get("pk")
    ).exists()
