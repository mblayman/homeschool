import datetime

import time_machine
from django.utils import timezone

from homeschool.courses.tests.factories import CourseFactory, CourseResourceFactory
from homeschool.schools.tests.factories import SchoolBreakFactory, SchoolYearFactory
from homeschool.students.tests.factories import (
    CourseworkFactory,
    EnrollmentFactory,
    GradeFactory,
)
from homeschool.test import TestCase


class TestReportsIndex(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("reports:index")

    def test_get(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("reports:index")

        assert self.get_context("nav_link") == "reports"

    def test_has_enrollments(self):
        """The enrollments are in the context."""
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)

        with self.login(user):
            self.get_check_200("reports:index")

        assert list(self.get_context("enrollments")) == [enrollment]

    def test_no_other_enrollments(self):
        """Another user's enrollments are not in the context."""
        user = self.make_user()
        EnrollmentFactory()

        with self.login(user):
            self.get_check_200("reports:index")

        assert list(self.get_context("enrollments")) == []

    def test_has_school_years(self):
        """The school years are in the context."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("reports:index")

        assert list(self.get_context("school_years")) == [school_year]

    def test_no_other_school_years(self):
        """Another user's school years are not in the context."""
        user = self.make_user()
        SchoolYearFactory()

        with self.login(user):
            self.get_check_200("reports:index")

        assert list(self.get_context("school_years")) == []


class TestBundleView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("reports:bundle", school_year.pk)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school__admin=user)

        with self.login(user):
            self.get_check_200("reports:bundle", school_year.pk)

        assert self.get_context("school_year") == school_year

    def test_no_other_school_years(self):
        """A user cannot access another user's bundle."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("reports:bundle", school_year.pk)

        self.response_404(response)


class TestCreateBundleView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("reports:bundle_create", school_year.pk)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school__admin=user)

        with self.login(user):
            response = self.get_check_200("reports:bundle_create", school_year.pk)

        assert response["Content-Type"] == "application/zip"
        assert "bundle.zip" in response["Content-Disposition"]

    def test_no_other_school_years(self):
        """A user cannot access another user's bundle."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("reports:bundle_create", school_year.pk)

        self.response_404(response)


class TestProgressReportView(TestCase):
    def test_unauthenticated_access(self):
        enrollment = EnrollmentFactory()
        self.assertLoginRequired("reports:progress", pk=enrollment.id)

    def test_get(self):
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)

        with self.login(user):
            self.get_check_200("reports:progress", pk=enrollment.id)

        assert self.get_context("grade_level") == enrollment.grade_level
        assert self.get_context("school_year") == enrollment.grade_level.school_year
        assert self.get_context("student") == enrollment.student

    def test_not_found_for_other_school(self):
        """A user cannot access a progress report that is not from their school."""
        user = self.make_user()
        enrollment = EnrollmentFactory()

        with self.login(user):
            response = self.get("reports:progress", pk=enrollment.id)

        self.response_404(response)

    def test_only_students_courses(self):
        """Only courses from the student are included."""
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)
        course = CourseFactory(grade_levels=[enrollment.grade_level])
        grade = GradeFactory(
            score=50,
            student=enrollment.student,
            graded_work__course_task__course=course,
        )
        grade_2 = GradeFactory(
            score=100,
            student=enrollment.student,
            graded_work__course_task__course=course,
        )
        GradeFactory(
            graded_work__course_task__course__grade_levels=[enrollment.grade_level]
        )

        with self.login(user):
            self.get_check_200("reports:progress", pk=enrollment.id)

        assert self.get_context("courses") == [
            {
                "course": grade.graded_work.course_task.course,
                "grades": [grade, grade_2],
                "course_average": 75,
            }
        ]

    def test_multiple_averages(self):
        """The average for each course is calculated."""
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)
        GradeFactory(
            score=50,
            student=enrollment.student,
            graded_work__course_task__course__grade_levels=[enrollment.grade_level],
        )
        GradeFactory(
            score=100,
            student=enrollment.student,
            graded_work__course_task__course__grade_levels=[enrollment.grade_level],
        )
        GradeFactory(
            graded_work__course_task__course__grade_levels=[enrollment.grade_level]
        )

        with self.login(user):
            self.get_check_200("reports:progress", pk=enrollment.id)

        assert self.get_context("courses")[0]["course_average"] == 50
        assert self.get_context("courses")[1]["course_average"] == 100

    def test_only_students_coursework(self):
        """Only coursework from the student is included.

        Coursework is added to the grades to display the completed dates.
        It is possible for a user to add a grade without the student finishing the task
        so the coursework can be None.
        """
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)
        grade = GradeFactory(
            student=enrollment.student,
            graded_work__course_task__course__grade_levels=[enrollment.grade_level],
        )
        CourseworkFactory(course_task=grade.graded_work.course_task)

        with self.login(user):
            self.get_check_200("reports:progress", pk=enrollment.id)

        assert self.get_context("courses")[0]["grades"][0].coursework is None

    def test_course_filter(self):
        """The report can filter to an individual course."""
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)
        student = enrollment.student
        course_1 = CourseFactory(grade_levels=[enrollment.grade_level])
        course_2 = CourseFactory(grade_levels=[enrollment.grade_level])
        GradeFactory(student=student, graded_work__course_task__course=course_1)
        GradeFactory(student=student, graded_work__course_task__course=course_2)
        url = self.reverse("reports:progress", pk=enrollment.id)
        url += f"?course={course_1.id}"

        with self.login(user):
            self.get_check_200(url)

        assert len(self.get_context("courses")) == 1


class TestResourceReportView(TestCase):
    def test_unauthenticated_access(self):
        enrollment = EnrollmentFactory()
        self.assertLoginRequired("reports:resource", pk=enrollment.id)

    def test_get(self):
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)
        course = CourseFactory(grade_levels=[enrollment.grade_level])
        resource = CourseResourceFactory(course=course)

        with self.login(user):
            self.get_check_200("reports:resource", pk=enrollment.id)

        assert self.get_context("grade_level") == enrollment.grade_level
        assert self.get_context("school_year") == enrollment.grade_level.school_year
        assert self.get_context("student") == enrollment.student
        assert list(self.get_context("resources")) == [resource]

    def test_not_found_for_other_school(self):
        """A user cannot access a progress report that is not from their school."""
        user = self.make_user()
        enrollment = EnrollmentFactory()

        with self.login(user):
            response = self.get("reports:resource", pk=enrollment.id)

        self.response_404(response)


class TestAttendanceReportView(TestCase):
    def test_unauthenticated_access(self):
        enrollment = EnrollmentFactory()
        self.assertLoginRequired("reports:attendance", pk=enrollment.id)

    def test_get(self):
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)

        with self.login(user):
            self.get_check_200("reports:attendance", pk=enrollment.id)

        assert self.get_context("grade_level") == enrollment.grade_level
        assert self.get_context("school_year") == enrollment.grade_level.school_year
        assert self.get_context("student") == enrollment.student

    @time_machine.travel("2021-04-01")  # A Thursday
    def test_school_dates(self):
        """The dates on the report have the expected states."""
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)
        school_year = enrollment.grade_level.school_year
        SchoolBreakFactory(
            school_year=school_year,
            start_date=school_year.start_date,
            end_date=school_year.start_date,
        )
        CourseworkFactory(
            student=enrollment.student,
            course_task__course__grade_levels=[enrollment.grade_level],
            completed_date=school_year.start_date + datetime.timedelta(days=1),
        )

        with self.login(user):
            self.get_check_200("reports:attendance", pk=enrollment.id)

        school_dates = self.get_context("school_dates")
        assert school_dates[0]["is_break"]
        assert school_dates[1]["attended"]
        assert not school_dates[4]["is_school_day"]  # First Saturday
        assert self.get_context("total_days_attended") == 1

    def test_school_year_end_date(self):
        """An old school year will go to the end date."""
        today = timezone.localdate()
        user = self.make_user()
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=today - datetime.timedelta(days=100),
            end_date=today - datetime.timedelta(days=50),
        )
        enrollment = EnrollmentFactory(grade_level__school_year=school_year)

        with self.login(user):
            self.get_check_200("reports:attendance", pk=enrollment.id)

        school_dates = self.get_context("school_dates")
        assert school_dates[-1]["date"] == school_year.end_date

    def test_future_school_year(self):
        """A future school year has no school dates."""
        today = timezone.localdate()
        user = self.make_user()
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + datetime.timedelta(days=50),
            end_date=today + datetime.timedelta(days=100),
        )
        enrollment = EnrollmentFactory(grade_level__school_year=school_year)

        with self.login(user):
            self.get_check_200("reports:attendance", pk=enrollment.id)

        assert not self.get_context("school_dates")

    def test_not_found_for_other_school(self):
        """A user cannot access an attendance report that is not from their school."""
        user = self.make_user()
        enrollment = EnrollmentFactory()

        with self.login(user):
            response = self.get("reports:attendance", pk=enrollment.id)

        self.response_404(response)
