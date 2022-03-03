from dataclasses import dataclass

from homeschool.courses.models import CourseResource
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.students.models import Student


@dataclass
class ResourceReportContext:
    resources: list[CourseResource]
    student: Student
    grade_level: GradeLevel
    school_year: SchoolYear

    @classmethod
    def from_enrollment(cls, enrollment):
        resources = (
            CourseResource.objects.filter(
                course__grade_levels__in=[enrollment.grade_level]
            )
            .select_related("course")
            .order_by("course")
        )
        return cls(
            resources,
            enrollment.student,
            enrollment.grade_level,
            enrollment.grade_level.school_year,
        )
