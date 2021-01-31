from typing import TYPE_CHECKING

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from .models import Student


class StudentMixin:
    """Add the ability to get a student from the URL."""

    if TYPE_CHECKING:  # pragma: no cover
        kwargs: dict = {}
        request = HttpRequest()

    @cached_property
    def student(self):
        return get_object_or_404(
            Student, uuid=self.kwargs["uuid"], school__admin=self.request.user
        )
