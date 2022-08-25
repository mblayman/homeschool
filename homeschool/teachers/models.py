from __future__ import annotations

from django.db import models

from homeschool.schools.models import SchoolYear


class Checklist(models.Model):
    """A checklist for teacher's to plan their work"""

    school_year = models.ForeignKey(
        "schools.SchoolYear", on_delete=models.CASCADE, related_name="checklists"
    )
    excluded_courses = models.JSONField(default=list, blank=True)

    @classmethod
    def filter_schedules(cls, school_year: SchoolYear, schedules: list) -> None:
        """Filter the schedules in place to remove any excluded courses."""
        checklist = cls.objects.filter(school_year=school_year).first()
        if not (checklist and checklist.excluded_courses):
            return None

        excluded_courses_set = set(checklist.excluded_courses)
        for schedule in schedules:
            courses = schedule["courses"]
            for course_info in reversed(courses):
                course = course_info["course"]
                if course.id in excluded_courses_set:
                    courses.remove(course_info)

    @classmethod
    def for_school_year(cls, school_year: SchoolYear) -> Checklist | None:
        """Get the checklist for the school year if it exists."""
        return cls.objects.filter(school_year=school_year).first()

    @classmethod
    def update(cls, school_year: SchoolYear, excluded_courses: list[str]) -> None:
        """Create or update a checklist for the school year."""
        cls.objects.update_or_create(
            school_year=school_year,
            defaults={
                "excluded_courses": [
                    str(course_id) for course_id in sorted(excluded_courses)
                ]
            },
        )
