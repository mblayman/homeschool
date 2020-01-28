import datetime
from unittest import mock

import pytz
from dateutil.relativedelta import MO, SU, relativedelta

from homeschool.courses.models import Course
from homeschool.courses.tests.factories import CourseFactory, CourseTaskFactory
from homeschool.schools.tests.factories import GradeLevelFactory, SchoolYearFactory
from homeschool.students.tests.factories import (
    CourseworkFactory,
    EnrollmentFactory,
    StudentFactory,
)
from homeschool.test import TestCase


class TestIndex(TestCase):
    def test_ok(self):
        self.get_check_200("core:index")


class TestApp(TestCase):
    def test_ok(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("core:app")

    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:app")

    @mock.patch("homeschool.core.views.timezone")
    def test_has_monday(self, timezone):
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        monday = now.date() + relativedelta(weekday=MO(-1))
        timezone.now.return_value = now

        with self.login(user):
            self.get("core:app")

        self.assertContext("monday", monday)

    @mock.patch("homeschool.core.views.timezone")
    def test_has_sunday(self, timezone):
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date() + relativedelta(weekday=SU(+1))
        timezone.now.return_value = now

        with self.login(user):
            self.get("core:app")

        self.assertContext("sunday", sunday)

    @mock.patch("homeschool.core.views.timezone")
    def test_has_schedules(self, timezone):
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date()
        monday = sunday - datetime.timedelta(days=6)
        timezone.now.return_value = now
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=sunday - datetime.timedelta(days=90),
            end_date=sunday + datetime.timedelta(days=90),
        )
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(
            grade_level=grade_level,
            days_of_week=Course.MONDAY
            + Course.WEDNESDAY
            + Course.THURSDAY
            + Course.FRIDAY,
        )
        task_1 = CourseTaskFactory(course=course)
        task_2 = CourseTaskFactory(course=course)
        task_3 = CourseTaskFactory(course=course)
        coursework = CourseworkFactory(
            student=student, course_task=task_1, completed_date=monday
        )
        EnrollmentFactory(student=student, grade_level=grade_level)

        with self.login(user), self.assertNumQueries(11):
            self.get("core:app")

        expected_schedule = {
            "student": student,
            "courses": [
                {
                    "course": course,
                    "days": [
                        {"coursework": [coursework]},
                        None,
                        {"task": task_2},
                        {"task": task_3},
                        None,
                    ],
                }
            ],
        }
        self.assertContext("schedules", [expected_schedule])

    def test_no_school_year(self):
        user = self.make_user()
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:app")

        self.assertContext("schedules", [])
