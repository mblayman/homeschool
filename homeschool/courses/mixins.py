from typing import TYPE_CHECKING

from django.http import Http404, HttpRequest
from django.utils.functional import cached_property

from homeschool.schools.models import GradeLevel

from .models import CourseTask


class CourseTaskMixin:
    """Add the ability to get a student from the URL."""

    if TYPE_CHECKING:  # pragma: no cover
        kwargs: dict = {}
        request = HttpRequest()

    @cached_property
    def course_task(self):
        grade_levels = GradeLevel.objects.filter(
            school_year__school__admin=self.request.user
        )
        task = (
            CourseTask.objects.filter(
                uuid=self.kwargs["course_task_uuid"],
                course__grade_levels__in=grade_levels,
            )
            .distinct()
            .first()
        )
        if not task:
            raise Http404
        return task
