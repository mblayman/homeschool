from django import forms

from homeschool.courses.models import Course

from .models import Checklist


class ChecklistForm(forms.Form):
    """Create a checklist with excluded courses."""

    def __init__(self, *args, **kwargs):
        self.school_year = kwargs.pop("school_year")
        super().__init__(*args, **kwargs)

    def save(self):
        """Create or update the checklist."""
        course_ids = set(
            Course.from_school_year(self.school_year).values_list("id", flat=True)
        )
        included_course_ids = {
            id_.removeprefix("course-")
            for id_ in self.data
            if id_.startswith("course-")
        }
        excluded_course_ids = list(course_ids - included_course_ids)
        Checklist.update(self.school_year, excluded_course_ids)
