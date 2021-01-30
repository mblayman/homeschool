import datetime

from homeschool.courses.tests.factories import CourseFactory, CourseTaskFactory
from homeschool.schools.tests.factories import GradeLevelFactory
from homeschool.students.forms import CourseworkForm, EnrollmentForm
from homeschool.students.models import Coursework
from homeschool.students.tests.factories import (
    CourseworkFactory,
    EnrollmentFactory,
    StudentFactory,
)
from homeschool.test import TestCase


class TestCourseworkForm(TestCase):
    def test_is_valid(self):
        """The coursework validates."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        course_task = CourseTaskFactory(course=course)
        data = {
            "student": str(student.id),
            "course_task": str(course_task.id),
            "completed_date": str(grade_level.school_year.start_date),
        }
        form = CourseworkForm(data=data)

        is_valid = form.is_valid()

        assert is_valid

    def test_student_can_create_coursework(self):
        """The student is enrolled in a course that contains the task."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        course_task = CourseTaskFactory(course=course)
        data = {
            "student": str(student.id),
            "course_task": str(course_task.id),
            "completed_date": str(grade_level.school_year.start_date),
        }
        form = CourseworkForm(data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert form.non_field_errors() == [
            "The student is not enrolled in this course."
        ]

    def test_save_new_coursework(self):
        """A new coursework is created for a student and task."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        course_task = CourseTaskFactory(course=course)
        data = {
            "student": str(student.id),
            "course_task": str(course_task.id),
            "completed_date": str(grade_level.school_year.start_date),
        }
        form = CourseworkForm(data=data)
        form.is_valid()

        form.save()

        assert (
            Coursework.objects.filter(student=student, course_task=course_task).count()
            == 1
        )

    def test_save_existing_coursework(self):
        """A new coursework is created for a student and task."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        course_task = CourseTaskFactory(course=course)
        CourseworkFactory(student=student, course_task=course_task)
        data = {
            "student": str(student.id),
            "course_task": str(course_task.id),
            "completed_date": str(grade_level.school_year.start_date),
        }
        form = CourseworkForm(data=data)
        form.is_valid()

        form.save()

        assert (
            Coursework.objects.filter(student=student, course_task=course_task).count()
            == 1
        )

    def test_completed_date_outside_school_year(self):
        """The completed data must be in the school year."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        course_task = CourseTaskFactory(course=course)
        data = {
            "student": str(student.id),
            "course_task": str(course_task.id),
            "completed_date": str(
                grade_level.school_year.start_date - datetime.timedelta(days=1)
            ),
        }
        form = CourseworkForm(data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert form.non_field_errors() == [
            "The completed date must be in the school year."
        ]

    def test_invalid_course_task(self):
        """An invalid student is an error."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory(course=course)
        data = {
            "student": str(student.id),
            "course_task": "0",
            "completed_date": str(grade_level.school_year.start_date),
        }
        form = CourseworkForm(data=data)

        is_valid = form.is_valid()

        assert not is_valid

    def test_invalid_completed_date(self):
        """An invalid completed date is an error."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        course_task = CourseTaskFactory(course=course)
        data = {
            "student": str(student.id),
            "course_task": str(course_task.id),
            "completed_date": "boom",
        }
        form = CourseworkForm(data=data)

        is_valid = form.is_valid()

        assert not is_valid


class TestEnrollmentForm(TestCase):
    def test_students_only_enroll_in_one_grade_level_per_year(self):
        """A student can only be enrolled in a single grade level in a school year."""
        user = self.make_user()
        enrollment = EnrollmentFactory(
            student__school=user.school, grade_level__school_year__school=user.school
        )
        another_grade_level = GradeLevelFactory(
            school_year=enrollment.grade_level.school_year
        )
        data = {
            "student": str(enrollment.student.id),
            "grade_level": str(another_grade_level.id),
        }
        form = EnrollmentForm(user=user, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert (
            "A student may not be enrolled in multiple grade levels in a school year. "
            f"{enrollment.student} is enrolled in {enrollment.grade_level}."
            in form.non_field_errors()
        )
