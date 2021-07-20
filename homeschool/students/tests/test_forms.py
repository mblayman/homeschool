import datetime

from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.schools.tests.factories import GradeLevelFactory
from homeschool.students.forms import CourseworkForm, EnrollmentForm, GradeForm
from homeschool.students.models import Coursework, Grade
from homeschool.students.tests.factories import (
    CourseworkFactory,
    EnrollmentFactory,
    GradeFactory,
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
        """An invalid course task is an error."""
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

    def test_no_grade_level(self):
        """A missing grade level raises a validation error."""
        user = self.make_user()
        school = user.school
        enrollment = EnrollmentFactory(
            student__school=school, grade_level__school_year__school=school
        )
        data = {"student": str(enrollment.student.id), "grade_level": "0"}
        form = EnrollmentForm(user=user, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "You need to select a grade level." in form.non_field_errors()


class TestGradeForm(TestCase):
    def test_is_valid(self):
        """The new grade validates."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        graded_work = GradedWorkFactory(course_task__course=course)
        data = {
            "student": str(student.id),
            "graded_work": str(graded_work.id),
            "score": "100",
        }
        form = GradeForm(data=data)

        is_valid = form.is_valid()

        assert is_valid

    def test_invalid_graded_work(self):
        """An invalid graded work is an error."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        GradedWorkFactory(course_task__course=course)
        data = {"student": str(student.id), "graded_work": "0", "score": "100"}
        form = GradeForm(data=data)

        is_valid = form.is_valid()

        assert not is_valid

    def test_save(self):
        """The form creates a new grade."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        graded_work = GradedWorkFactory(course_task__course=course)
        data = {
            "student": str(student.id),
            "graded_work": str(graded_work.id),
            "score": "100",
        }
        form = GradeForm(data=data)
        form.is_valid()

        form.save()

        assert (
            Grade.objects.filter(
                student=student, graded_work=graded_work, score=100
            ).count()
            == 1
        )

    def test_save_update(self):
        """The form updates a grade."""
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        graded_work = GradedWorkFactory(course_task__course=course)
        GradeFactory(student=student, graded_work=graded_work)
        data = {
            "student": str(student.id),
            "graded_work": str(graded_work.id),
            "score": "100",
        }
        form = GradeForm(data=data)
        form.is_valid()

        form.save()

        assert (
            Grade.objects.filter(student=student, graded_work=graded_work).count() == 1
        )
