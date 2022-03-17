from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Q

from homeschool.courses.models import Course, CourseResource
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.students.models import Coursework, Enrollment, Grade, Student


@dataclass
class ProgressReportContext:
    student: Student
    grade_level: GradeLevel
    school_year: SchoolYear
    courses: list[dict]

    @classmethod
    def from_enrollment(
        cls, enrollment: Enrollment, course_id: Course | None = None
    ) -> ProgressReportContext:
        if course_id:
            qs_filter = Q(graded_work__course_task__course__id=course_id)
        else:
            qs_filter = Q(
                graded_work__course_task__course__grade_levels__in=[
                    enrollment.grade_level
                ]
            )

        grades = (
            Grade.objects.filter(qs_filter, student=enrollment.student)
            # Include secondary ordering so tasks are ordered in the course.
            .order_by(
                "graded_work__course_task__course", "graded_work__course_task"
            ).select_related(
                "graded_work__course_task", "graded_work__course_task__course"
            )
        )

        cls._mixin_coursework(grades, enrollment.student)
        courses = cls._build_courses_info(grades)
        return cls(
            enrollment.student,
            enrollment.grade_level,
            enrollment.grade_level.school_year,
            courses,
        )

    @classmethod
    def _mixin_coursework(cls, grades, student):
        """Mix in the coursework for the grades.

        Coursework is added to the grades to display the completed dates.
        It is possible for a user to add a grade without the student finishing the task
        so the coursework can be None.
        """
        tasks = [grade.graded_work.course_task for grade in grades]
        coursework_by_task_id = {
            coursework.course_task_id: coursework
            for coursework in Coursework.objects.filter(
                student=student, course_task__in=tasks
            )
        }
        for grade in grades:
            grade.coursework = coursework_by_task_id.get(
                grade.graded_work.course_task_id
            )

    @classmethod
    def _build_courses_info(cls, grades):
        """Regroup the grades into an appropriate display structure for the template.

        Grades must be sorted by course.
        """
        if not grades:
            return []

        courses = []
        course = None
        course_info = {}
        for grade in grades:
            next_course = grade.graded_work.course_task.course
            if course != next_course:
                # Don't compute average until a course is collected.
                # On the first iteration when course is None, nothing is collected yet.
                if course is not None:
                    cls._compute_course_average(course_info)
                course = next_course
                course_info = {"course": course, "grades": [grade]}
                courses.append(course_info)
            else:
                course_info["grades"].append(grade)

        # Compute average of last course to catch the edge case.
        cls._compute_course_average(course_info)
        return courses

    @classmethod
    def _compute_course_average(self, course_info):
        """Compute the average for the course based on collected grades."""
        grades = course_info["grades"]
        average = sum(grade.score for grade in grades) / len(grades)
        # Sane rounding.
        course_info["course_average"] = int(Decimal(average).quantize(0, ROUND_HALF_UP))


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
