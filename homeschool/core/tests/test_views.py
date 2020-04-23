import datetime
from unittest import mock

import pytz
from dateutil.relativedelta import MO, SU, relativedelta
from django.utils import timezone

from homeschool.courses.models import Course
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolFactory,
    SchoolYearFactory,
)
from homeschool.students.models import Coursework
from homeschool.students.tests.factories import (
    CourseworkFactory,
    EnrollmentFactory,
    GradeFactory,
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

    @mock.patch("homeschool.users.models.timezone")
    def test_has_monday(self, timezone):
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        monday = now.date() + relativedelta(weekday=MO(-1))
        timezone.localdate.return_value = now.date()

        with self.login(user):
            self.get("core:app")

        self.assertContext("monday", monday)

    @mock.patch("homeschool.users.models.timezone")
    def test_has_sunday(self, timezone):
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date() + relativedelta(weekday=SU(+1))
        timezone.localdate.return_value = now.date()

        with self.login(user):
            self.get("core:app")

        self.assertContext("sunday", sunday)

    @mock.patch("homeschool.users.models.timezone")
    def test_has_previous_week_date(self, timezone):
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        monday = now.date() + relativedelta(weekday=MO(-1))
        previous_monday = monday - datetime.timedelta(days=7)
        timezone.localdate.return_value = now.date()

        with self.login(user):
            self.get("core:app")

        self.assertContext("previous_week_date", previous_monday)

    @mock.patch("homeschool.users.models.timezone")
    def test_has_next_week_date(self, timezone):
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        monday = now.date() + relativedelta(weekday=MO(-1))
        next_monday = monday + datetime.timedelta(days=7)
        timezone.localdate.return_value = now.date()

        with self.login(user):
            self.get("core:app")

        self.assertContext("next_week_date", next_monday)

    @mock.patch("homeschool.users.models.timezone")
    def test_has_today(self, timezone):
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        timezone.localdate.return_value = now.date()
        today = now.date()
        user = self.make_user()
        SchoolYearFactory(
            school=user.school,
            start_date=today - datetime.timedelta(days=90),
            end_date=today + datetime.timedelta(days=90),
        )

        with self.login(user):
            self.get("core:app")

        self.assertContext("day", today)

    @mock.patch("homeschool.users.models.timezone")
    def test_school_year_for_user_only(self, timezone):
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date()
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        SchoolYearFactory(
            start_date=sunday - datetime.timedelta(days=90),
            end_date=sunday + datetime.timedelta(days=90),
        )
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=sunday - datetime.timedelta(days=90),
            end_date=sunday + datetime.timedelta(days=90),
            days_of_week=SchoolYear.MONDAY
            + SchoolYear.TUESDAY
            + SchoolYear.WEDNESDAY
            + SchoolYear.THURSDAY
            + SchoolYear.FRIDAY,
        )
        grade_level = GradeLevelFactory(school_year=school_year)
        CourseFactory(grade_level=grade_level)
        EnrollmentFactory(student=student, grade_level=grade_level)

        with self.login(user):
            self.get("core:app")

        schedules = self.get_context("schedules")
        self.assertTrue(len(schedules[0]["courses"]) > 0)

    @mock.patch("homeschool.users.models.timezone")
    def test_has_schedules(self, timezone):
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date()
        monday = sunday - datetime.timedelta(days=6)
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=sunday - datetime.timedelta(days=90),
            end_date=sunday + datetime.timedelta(days=90),
            days_of_week=SchoolYear.MONDAY
            + SchoolYear.TUESDAY
            + SchoolYear.WEDNESDAY
            + SchoolYear.THURSDAY
            + SchoolYear.FRIDAY,
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
                        {"week_date": monday, "coursework": [coursework]},
                        {"week_date": monday + datetime.timedelta(days=1)},
                        {
                            "week_date": monday + datetime.timedelta(days=2),
                            "task": task_2,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=3),
                            "task": task_3,
                        },
                        {"week_date": monday + datetime.timedelta(days=4)},
                    ],
                }
            ],
        }
        self.assertContext("schedules", [expected_schedule])

    @mock.patch("homeschool.users.models.timezone")
    def test_has_week_dates(self, timezone):
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date()
        monday = sunday - datetime.timedelta(days=6)
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        SchoolYearFactory(
            school=user.school,
            start_date=sunday - datetime.timedelta(days=90),
            end_date=sunday + datetime.timedelta(days=90),
            days_of_week=SchoolYear.MONDAY
            + SchoolYear.TUESDAY
            + SchoolYear.WEDNESDAY
            + SchoolYear.THURSDAY
            + SchoolYear.FRIDAY,
        )

        with self.login(user):
            self.get("core:app")

        expected_week_dates = [
            monday,
            monday + datetime.timedelta(days=1),
            monday + datetime.timedelta(days=2),
            monday + datetime.timedelta(days=3),
            monday + datetime.timedelta(days=4),
        ]
        self.assertContext("week_dates", expected_week_dates)

    def test_no_school_year(self):
        user = self.make_user()
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:app")

        self.assertContext("schedules", [])

    @mock.patch("homeschool.users.models.timezone")
    def test_weekly(self, timezone):
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date()
        monday = sunday - datetime.timedelta(days=6)
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=sunday - datetime.timedelta(days=90),
            end_date=sunday + datetime.timedelta(days=90),
            days_of_week=SchoolYear.MONDAY
            + SchoolYear.TUESDAY
            + SchoolYear.WEDNESDAY
            + SchoolYear.THURSDAY
            + SchoolYear.FRIDAY,
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
        CourseTaskFactory(course=course)
        CourseTaskFactory(course=course)
        CourseTaskFactory(course=course)
        task_2 = CourseTaskFactory(course=course)
        CourseworkFactory(student=student, course_task=task_1, completed_date=monday)
        EnrollmentFactory(student=student, grade_level=grade_level)

        with self.login(user), self.assertNumQueries(12):
            self.get("core:weekly", year=2020, month=1, day=27)

        expected_schedule = {
            "student": student,
            "courses": [
                {
                    "course": course,
                    "days": [
                        {
                            "week_date": monday + datetime.timedelta(days=7),
                            "task": task_2,
                        },
                        {"week_date": monday + datetime.timedelta(days=8)},
                        {"week_date": monday + datetime.timedelta(days=9)},
                        {"week_date": monday + datetime.timedelta(days=10)},
                        {"week_date": monday + datetime.timedelta(days=11)},
                    ],
                }
            ],
        }
        self.assertContext("schedules", [expected_schedule])

    @mock.patch("homeschool.users.models.timezone")
    def test_when_weekly_includes_today(self, timezone):
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        timezone.localdate.return_value = now.date()
        today = now.date()
        user = self.make_user()
        SchoolYearFactory(
            school=user.school,
            start_date=today - datetime.timedelta(days=90),
            end_date=today + datetime.timedelta(days=90),
        )

        with self.login(user):
            self.get("core:weekly", year=2020, month=1, day=20)

        self.assertContext("day", today)

    @mock.patch("homeschool.users.models.timezone")
    def test_no_tasks_in_past_week(self, timezone):
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date()
        monday = sunday - datetime.timedelta(days=6)
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=sunday - datetime.timedelta(days=90),
            end_date=sunday + datetime.timedelta(days=90),
            days_of_week=SchoolYear.MONDAY
            + SchoolYear.TUESDAY
            + SchoolYear.WEDNESDAY
            + SchoolYear.THURSDAY
            + SchoolYear.FRIDAY,
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
        CourseTaskFactory(course=course)
        CourseworkFactory(
            student=student,
            course_task=task_1,
            completed_date=monday - datetime.timedelta(days=7),
        )
        EnrollmentFactory(student=student, grade_level=grade_level)

        with self.login(user):
            self.get("core:weekly", year=2020, month=1, day=13)

        schedules = self.get_context("schedules")
        # Day 0 has coursework. Day 1 should show no task.
        self.assertNotIn("task", schedules[0]["courses"][0]["days"][1])


class TestDaily(TestCase):
    def test_ok(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("core:daily")

    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:daily")

    def test_has_day(self):
        user = self.make_user()
        today = timezone.now().date()

        with self.login(user):
            self.get("core:daily")

        self.assertContext("day", today)

    def test_no_school_year(self):
        user = self.make_user()
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:daily")

        self.assertContext("schedules", [])

    @mock.patch("homeschool.users.models.timezone")
    def test_school_not_run_on_day(self, timezone):
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date()
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        SchoolYearFactory(
            school=user.school,
            start_date=sunday - datetime.timedelta(days=90),
            end_date=sunday + datetime.timedelta(days=90),
            days_of_week=SchoolYear.MONDAY,
        )

        with self.login(user):
            self.get("core:daily")

        self.assertContext("schedules", [])

    @mock.patch("homeschool.users.models.timezone")
    def test_school_year_for_user_only(self, timezone):
        now = datetime.datetime(2020, 1, 24, tzinfo=pytz.utc)
        friday = now.date()
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        StudentFactory(school=user.school)
        SchoolYearFactory(
            start_date=friday - datetime.timedelta(days=90),
            end_date=friday + datetime.timedelta(days=90),
            days_of_week=SchoolYear.MONDAY,
        )
        SchoolYearFactory(
            school=user.school,
            start_date=friday - datetime.timedelta(days=90),
            end_date=friday + datetime.timedelta(days=90),
            days_of_week=SchoolYear.FRIDAY,
        )

        with self.login(user):
            self.get("core:daily")

        schedules = self.get_context("schedules")
        self.assertNotEqual(schedules, [])

    @mock.patch("homeschool.users.models.timezone")
    def test_has_schedules(self, timezone):
        now = datetime.datetime(2020, 1, 24, tzinfo=pytz.utc)
        friday = now.date()
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=friday - datetime.timedelta(days=90),
            end_date=friday + datetime.timedelta(days=90),
            days_of_week=SchoolYear.FRIDAY,
        )
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(grade_level=grade_level, days_of_week=Course.FRIDAY)
        task_1 = CourseTaskFactory(course=course)
        coursework = CourseworkFactory(
            student=student, course_task=task_1, completed_date=friday
        )
        course_2 = CourseFactory(grade_level=grade_level, days_of_week=Course.FRIDAY)
        task_2a = CourseTaskFactory(course=course_2)
        CourseworkFactory(
            student=student,
            course_task=task_2a,
            completed_date=friday - datetime.timedelta(days=1),
        )
        task_2b = CourseTaskFactory(course=course_2)
        course_3 = CourseFactory(grade_level=grade_level, days_of_week=Course.THURSDAY)
        CourseTaskFactory(course=course_3)
        course_4 = CourseFactory(grade_level=grade_level, days_of_week=Course.FRIDAY)
        EnrollmentFactory(student=student, grade_level=grade_level)

        with self.login(user):
            self.get("core:daily")

        expected_schedule = {
            "student": student,
            "courses": [
                {"course": course, "coursework": [coursework]},
                {"course": course_2, "task": task_2b},
                {"course": course_3},
                {"course": course_4, "task": None},
            ],
        }
        self.assertContext("schedules", [expected_schedule])

    @mock.patch("homeschool.users.models.timezone")
    def test_far_future_day_schedule(self, timezone):
        now = datetime.datetime(2020, 1, 23, tzinfo=pytz.utc)
        thursday = now.date()
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=thursday - datetime.timedelta(days=90),
            end_date=thursday + datetime.timedelta(days=90),
        )
        course = CourseFactory(grade_level__school_year=school_year)
        CourseworkFactory(
            student=student,
            course_task__course=course,
            completed_date=thursday - datetime.timedelta(days=1),
        )
        CourseTaskFactory(course=course)  # current task for thursday
        CourseTaskFactory(course=course)  # projected task for friday
        task = CourseTaskFactory(course=course)
        EnrollmentFactory(student=student, grade_level=course.grade_level)

        with self.login(user):
            self.get("core:daily_for_date", year=2020, month=1, day=27)

        expected_schedule = {
            "student": student,
            "courses": [{"course": course, "task": task}],
        }
        self.assertContext("schedules", [expected_schedule])

    def test_specific_day(self):
        user = self.make_user()
        day = datetime.date(2020, 1, 20)

        with self.login(user):
            self.get("core:daily_for_date", year=day.year, month=day.month, day=day.day)

        self.assertContext("day", day)

    def test_surrounding_dates_no_school_year(self):
        user = self.make_user()
        today = timezone.now().date()

        with self.login(user):
            self.get("core:daily")

        self.assertContext("ereyesterday", today - datetime.timedelta(days=2))
        self.assertContext("yesterday", today - datetime.timedelta(days=1))
        self.assertContext("tomorrow", today + datetime.timedelta(days=1))
        self.assertContext("overmorrow", today + datetime.timedelta(days=2))

    @mock.patch("homeschool.users.models.timezone")
    def test_surrounding_dates(self, timezone):
        now = datetime.datetime(2020, 1, 22, tzinfo=pytz.utc)
        wednesday = now.date()
        timezone.localdate.return_value = wednesday
        user = self.make_user()
        SchoolYearFactory(
            school=user.school,
            start_date=wednesday - datetime.timedelta(days=90),
            end_date=wednesday + datetime.timedelta(days=90),
            days_of_week=SchoolYear.TUESDAY
            + SchoolYear.WEDNESDAY
            + SchoolYear.THURSDAY,
        )

        with self.login(user):
            self.get("core:daily")

        previous_thursday = wednesday - datetime.timedelta(days=6)
        self.assertContext("ereyesterday", previous_thursday)
        self.assertContext("yesterday", wednesday - datetime.timedelta(days=1))
        self.assertContext("tomorrow", wednesday + datetime.timedelta(days=1))
        next_tuesday = wednesday + datetime.timedelta(days=6)
        self.assertContext("overmorrow", next_tuesday)

    def test_complete_daily(self):
        today = timezone.now().date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        task = CourseTaskFactory(course__grade_level__school_year__school=user.school)
        data = {
            "completed_date": "{:%Y-%m-%d}".format(today),
            f"task-{student.id}-{task.id}": "on",
        }

        with self.login(user):
            self.post("core:daily", data=data)

        self.assertTrue(
            Coursework.objects.filter(
                student=student, course_task=task, completed_date=today
            ).exists()
        )

    def test_incomplete_daily(self):
        today = timezone.now().date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        task = CourseTaskFactory(course__grade_level__school_year__school=user.school)
        CourseworkFactory(student=student, course_task=task)
        data = {
            "completed_date": "{:%Y-%m-%d}".format(today),
            f"task-{student.id}-{task.id}": "off",
        }

        with self.login(user):
            self.post("core:daily", data=data)

        self.assertFalse(
            Coursework.objects.filter(student=student, course_task=task).exists()
        )

    def test_to_grade(self):
        today = timezone.now().date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        graded_work = GradedWorkFactory(
            course_task__course__grade_level__school_year__school=user.school
        )
        data = {
            "completed_date": "{:%Y-%m-%d}".format(today),
            f"task-{student.id}-{graded_work.course_task.id}": "on",
        }

        with self.login(user):
            response = self.post("core:daily", data=data)

        self.response_302(response)
        url = self.reverse("students:grade")
        self.assertIn(url, response.get("Location"))

    def test_no_grade_when_already_graded(self):
        today = timezone.now().date()
        user = self.make_user()
        school = user.school
        student = StudentFactory(school=school)
        grade = GradeFactory(
            student=student,
            graded_work__course_task__course__grade_level__school_year__school=school,
        )
        data = {
            "completed_date": "{:%Y-%m-%d}".format(today),
            f"task-{student.id}-{grade.graded_work.course_task.id}": "on",
        }

        with self.login(user):
            response = self.post("core:daily", data=data)

        self.response_302(response)
        self.assertEqual(response.get("Location"), self.reverse("core:daily"))


class TestStartView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:start")

    def test_ok(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("core:start")


class TestStartSchoolYearView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:start-school-year")

    def test_ok(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("core:start-school-year")

    def test_valid_submission(self):
        user = self.make_user()
        data = {
            "school": str(user.school.id),
            "start_date": "1/1/20",
            "end_date": "12/31/20",
        }

        with self.login(user):
            response = self.post("core:start-school-year", data=data)

        self.assertEqual(SchoolYear.objects.filter(school=user.school).count(), 1)
        self.response_302(response)
        self.assertEqual(
            response.get("Location"), self.reverse("core:start-grade-level")
        )

    def test_start_date_before_end_date(self):
        user = self.make_user()
        data = {
            "school": str(user.school.id),
            "start_date": "12/31/20",
            "end_date": "1/1/20",
        }

        with self.login(user):
            response = self.post("core:start-school-year", data=data)

        self.response_200(response)
        form = self.get_context("form")
        self.assertEqual(
            form.non_field_errors(), ["The start date must be before the end date."]
        )

    def test_only_school_for_user(self):
        school = SchoolFactory()
        user = self.make_user()
        data = {
            "school": str(school.id),
            "start_date": "1/1/20",
            "end_date": "12/31/20",
        }

        with self.login(user):
            response = self.post("core:start-school-year", data=data)

        self.response_200(response)
        form = self.get_context("form")
        self.assertEqual(
            form.non_field_errors(),
            ["A school year cannot be created for a different school."],
        )

    def test_has_school_year(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get("core:start-school-year")

        self.assertContext("school_year", school_year)


class TestStartGradeLevelView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:start-grade-level")

    def test_ok(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("core:start-grade-level")

    def test_has_school_year(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get("core:start-grade-level")

        self.assertContext("school_year", school_year)

    def test_has_grade_level(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)

        with self.login(user):
            self.get("core:start-grade-level")

        self.assertContext("grade_level", grade_level)

    def test_valid_submission(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        data = {"school_year": str(school_year.id), "name": "Kindergarten"}

        with self.login(user):
            response = self.post("core:start-grade-level", data=data)

        self.assertEqual(GradeLevel.objects.filter(school_year=school_year).count(), 1)
        self.response_302(response)
        self.assertEqual(response.get("Location"), self.reverse("core:start-course"))

    def test_only_school_year_for_user(self):
        user = self.make_user()
        school_year = SchoolYearFactory()
        data = {"school_year": str(school_year.id), "name": "Kindergarten"}

        with self.login(user):
            response = self.post("core:start-grade-level", data=data)

        self.response_200(response)
        form = self.get_context("form")
        self.assertEqual(
            form.non_field_errors(),
            ["A grade level cannot be created for a different user's school year."],
        )

    def test_bogus_school_year(self):
        user = self.make_user()
        data = {"school_year": "0", "name": "Kindergarten"}

        with self.login(user):
            response = self.post("core:start-grade-level", data=data)

        self.response_200(response)
        form = self.get_context("form")
        self.assertEqual(form.non_field_errors(), ["Invalid school year."])
