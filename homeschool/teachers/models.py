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
