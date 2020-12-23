import datetime
from unittest import mock

import pytest
import pytz
from dateutil.relativedelta import FR, MO, SA, SU, WE, relativedelta
from django.contrib import messages
from django.contrib.messages.storage.base import Message
from django.contrib.messages.storage.cookie import CookieStorage
from django.utils import timezone

from homeschool.core.schedules import Week
from homeschool.courses.models import Course, CourseTask
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.notifications.models import Notification
from homeschool.notifications.tests.factories import NotificationFactory
from homeschool.schools.models import GradeLevel, SchoolBreak, SchoolYear
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolBreakFactory,
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
from homeschool.users.tests.factories import UserFactory


class TestIndex(TestCase):
    def test_ok(self):
        self.get_check_200("core:index")


class TestAbout(TestCase):
    def test_ok(self):
        self.get_check_200("core:about")


class TestPrivacy(TestCase):
    def test_ok(self):
        self.get_check_200("core:privacy")


class TestTerms(TestCase):
    def test_ok(self):
        self.get_check_200("core:terms")


class TestApp(TestCase):
    def make_student_enrolled_in_grade_level(self, user, week_date):
        enrollment = EnrollmentFactory(
            grade_level__school_year__school=user.school,
            grade_level__school_year__start_date=(
                week_date - datetime.timedelta(days=90)
            ),
            grade_level__school_year__end_date=(
                week_date + datetime.timedelta(days=90)
            ),
            student__school=user.school,
        )
        return enrollment.student, enrollment.grade_level

    def test_ok(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("core:app")

    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:app")

    @mock.patch("homeschool.users.models.timezone")
    def test_has_days(self, timezone):
        """The context has the first and last day of the week."""
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        first_day = now.date() + relativedelta(weekday=SU(-1))
        last_day = now.date() + relativedelta(weekday=SA(+1))
        timezone.localdate.return_value = now.date()
        SchoolYearFactory(
            school=user.school,
            start_date=now,
            end_date=now + datetime.timedelta(days=1),
        )
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:app")

        assert self.get_context("first_day") == first_day
        assert self.get_context("last_day") == last_day

    @mock.patch("homeschool.users.models.timezone")
    def test_has_surrounding_week_dates(self, timezone):
        """The context has the previous and next week dates."""
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date() + relativedelta(weekday=SU(-1))
        previous_sunday = sunday - datetime.timedelta(days=7)
        next_sunday = sunday + datetime.timedelta(days=7)
        timezone.localdate.return_value = now.date()
        SchoolYearFactory(
            school=user.school,
            start_date=now,
            end_date=now + datetime.timedelta(days=1),
        )
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:app")

        assert self.get_context("previous_week_date") == previous_sunday
        assert self.get_context("next_week_date") == next_sunday

    @mock.patch("homeschool.users.models.timezone")
    def test_has_today(self, mock_timezone):
        today = timezone.localdate()
        mock_timezone.localdate.return_value = today
        user = self.make_user()
        SchoolYearFactory(school=user.school)
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:app")

        self.assertContext("day", today)

    @mock.patch("homeschool.users.models.timezone")
    def test_school_year_for_user_only(self, mock_timezone):
        sunday = timezone.localdate() + relativedelta(weekday=SU)
        mock_timezone.localdate.return_value = sunday
        user = self.make_user()
        student, grade_level = self.make_student_enrolled_in_grade_level(user, sunday)
        SchoolYearFactory()
        CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get("core:app")

        schedules = self.get_context("schedules")
        assert len(schedules[0]["courses"]) > 0
        assert self.get_context("school_year") == grade_level.school_year

    @mock.patch("homeschool.users.models.timezone")
    def test_has_schedules(self, timezone):
        """The schedules are in the context."""
        now = datetime.datetime(2020, 1, 24, tzinfo=pytz.utc)
        friday = now.date()
        monday = friday - datetime.timedelta(days=4)
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student, grade_level = self.make_student_enrolled_in_grade_level(user, friday)
        course = CourseFactory(
            grade_levels=[grade_level],
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
        school_break = SchoolBreakFactory(
            school_year=grade_level.school_year,
            start_date=monday + datetime.timedelta(days=4),
            end_date=monday + datetime.timedelta(days=4),
        )

        with self.login(user), self.assertNumQueries(16):
            self.get("core:app")

        expected_schedule = {
            "student": student,
            "courses": [
                {
                    "course": course,
                    "days": [
                        {
                            "week_date": monday,
                            "coursework": [coursework],
                            "school_break": None,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=1),
                            "school_break": None,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=2),
                            "task": task_2,
                            "school_break": None,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=3),
                            "task": task_3,
                            "school_break": None,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=4),
                            "school_break": school_break,
                            "date_type": SchoolBreak.DateType.SINGLE,
                        },
                    ],
                }
            ],
        }
        schedules = self.get_context("schedules")
        assert schedules == [expected_schedule]

    @mock.patch("homeschool.users.models.timezone")
    def test_has_week_dates(self, mock_timezone):
        sunday = timezone.localdate() + relativedelta(weekday=SU)
        monday = sunday + datetime.timedelta(days=1)
        mock_timezone.localdate.return_value = sunday
        user = self.make_user()
        SchoolYearFactory(
            school=user.school,
            days_of_week=SchoolYear.MONDAY
            + SchoolYear.TUESDAY
            + SchoolYear.WEDNESDAY
            + SchoolYear.THURSDAY
            + SchoolYear.FRIDAY,
        )
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:app")

        assert self.get_context("week_dates") == [
            {"date": monday, "school_break": None},
            {"date": monday + datetime.timedelta(days=1), "school_break": None},
            {"date": monday + datetime.timedelta(days=2), "school_break": None},
            {"date": monday + datetime.timedelta(days=3), "school_break": None},
            {"date": monday + datetime.timedelta(days=4), "school_break": None},
        ]

    @mock.patch("homeschool.users.models.timezone")
    def test_weekly(self, timezone):
        """The weekly schedule is available in the context."""
        now = datetime.datetime(2020, 1, 24, tzinfo=pytz.utc)  # A Friday
        friday = now.date()
        monday = friday - datetime.timedelta(days=4)
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student, grade_level = self.make_student_enrolled_in_grade_level(user, friday)
        course = CourseFactory(
            grade_levels=[grade_level],
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

        with self.login(user), self.assertNumQueries(17):
            self.get("core:weekly", year=2020, month=1, day=27)

        expected_schedule = {
            "student": student,
            "courses": [
                {
                    "course": course,
                    "days": [
                        {
                            "week_date": monday + datetime.timedelta(days=7),
                            "school_break": None,
                            "task": task_2,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=8),
                            "school_break": None,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=9),
                            "school_break": None,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=10),
                            "school_break": None,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=11),
                            "school_break": None,
                        },
                    ],
                }
            ],
        }
        assert self.get_context("schedules") == [expected_schedule]

    @mock.patch("homeschool.users.models.timezone")
    def test_when_weekly_includes_today(self, mock_timezone):
        today = timezone.localdate() + relativedelta(weekday=SU)
        monday = today + relativedelta(weekday=MO(1))
        mock_timezone.localdate.return_value = today
        user = self.make_user()
        SchoolYearFactory(school=user.school)
        StudentFactory(school=user.school)

        with self.login(user):
            self.get(
                "core:weekly", year=monday.year, month=monday.month, day=monday.day
            )

        self.assertContext("day", today)

    @mock.patch("homeschool.users.models.timezone")
    def test_no_tasks_in_past_week(self, timezone):
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date()
        monday = sunday - datetime.timedelta(days=6)
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student, grade_level = self.make_student_enrolled_in_grade_level(user, sunday)
        course = CourseFactory(
            grade_levels=[grade_level],
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

        with self.login(user):
            self.get("core:weekly", year=2020, month=1, day=13)

        schedules = self.get_context("schedules")
        # Day 0 has coursework. Day 1 should show no task.
        assert "task" not in schedules[0]["courses"][0]["days"][1]

    @mock.patch("homeschool.users.models.timezone")
    def test_do_not_show_course_when_no_days(self, timezone):
        now = datetime.datetime(2020, 1, 23, tzinfo=pytz.utc)
        thursday = now.date()
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student, grade_level = self.make_student_enrolled_in_grade_level(user, thursday)
        course = CourseFactory(grade_levels=[grade_level], days_of_week=Course.NO_DAYS)
        CourseTaskFactory(course=course)

        with self.login(user):
            self.get("core:app")

        schedules = self.get_context("schedules")
        assert schedules[0]["courses"] == []

    @mock.patch("homeschool.users.models.timezone")
    def test_show_course_when_no_days_in_past(self, timezone):
        """When the week is in the past, show the course, even if it's not running."""
        now = datetime.datetime(2020, 1, 25, tzinfo=pytz.utc)
        saturday = now.date()
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student, grade_level = self.make_student_enrolled_in_grade_level(user, saturday)
        course = CourseFactory(grade_levels=[grade_level], days_of_week=Course.NO_DAYS)
        CourseTaskFactory(course=course)

        with self.login(user):
            self.get("core:app")

        schedules = self.get_context("schedules")
        assert schedules[0]["courses"]

    def test_schedules_in_grade_level_order(self):
        """The schedules are in the same order as the grade levels."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year=school_year)
        grade_level_2 = GradeLevelFactory(school_year=school_year)
        enrollment = EnrollmentFactory(
            grade_level=grade_level_2, student__school=user.school
        )
        enrollment_2 = EnrollmentFactory(grade_level=grade_level)

        with self.login(user):
            self.get("core:app")

        schedules = self.get_context("schedules")
        assert schedules[0]["student"] == enrollment_2.student
        assert schedules[1]["student"] == enrollment.student

    def test_future_school_year(self):
        """A future school year shows the task in a week at the school year start."""
        today = timezone.localdate()
        user = self.make_user()
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + relativedelta(years=1, month=1, day=1),
            end_date=today + relativedelta(years=1, month=12, day=31),
            days_of_week=SchoolYear.ALL_DAYS,
        )
        enrollment = EnrollmentFactory(
            grade_level__school_year=school_year, student__school=user.school
        )
        task = CourseTaskFactory(course__grade_levels=[enrollment.grade_level])
        week = Week(school_year.start_date)

        with self.login(user):
            self.get(
                "core:weekly",
                year=week.first_day.year,
                month=week.first_day.month,
                day=week.first_day.day,
            )

        schedule = self.get_context("next_year_schedules")[0]
        course_day = {}
        for course_schedule_item in schedule["courses"][0]["days"]:
            if course_schedule_item["week_date"] == school_year.start_date:
                course_day = course_schedule_item
        assert course_day["task"] == task
        assert self.get_context("school_year") == school_year

    def test_future_school_year_advanced_week(self):
        """Looking ahead in a future school year calculates offsets from year start.

        This is slightly different from looking at the first week of a school year
        that has a starting day before the school year starts. The primary functional
        difference is that the future school year will appear in the `schedules`
        context instead of `next_year_schedules` context.
        """
        today = timezone.localdate()
        user = self.make_user()
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + relativedelta(years=1, month=1, day=1),
            end_date=today + relativedelta(years=1, month=12, day=31),
            # Running only on the last possible day should guarantee 1 task/week.
            days_of_week=SchoolYear.SATURDAY,
        )
        enrollment = EnrollmentFactory(
            grade_level__school_year=school_year, student__school=user.school
        )
        course = CourseFactory(
            grade_levels=[enrollment.grade_level], days_of_week=Course.SATURDAY
        )
        CourseTaskFactory(course=course)
        task = CourseTaskFactory(course=course)
        week = Week(school_year.start_date)
        first_day = week.first_day + datetime.timedelta(days=7)

        with self.login(user):
            self.get(
                "core:weekly",
                year=first_day.year,
                month=first_day.month,
                day=first_day.day,
            )

        schedule = self.get_context("schedules")[0]
        assert schedule["courses"][0]["days"][0]["task"] == task

    def test_two_school_years_same_week(self):
        """When two school years are in the same week, both are in the context."""
        today = timezone.localdate()
        user = self.make_user()
        current_school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + relativedelta(month=1, day=1),
            end_date=today + relativedelta(month=12, day=31),
            days_of_week=SchoolYear.ALL_DAYS,
        )
        enrollment = EnrollmentFactory(grade_level__school_year=current_school_year)
        CourseTaskFactory(course__grade_levels=[enrollment.grade_level])
        next_school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + relativedelta(years=1, month=1, day=1),
            end_date=today + relativedelta(years=1, month=12, day=31),
            days_of_week=SchoolYear.ALL_DAYS,
        )
        enrollment = EnrollmentFactory(
            grade_level__school_year=next_school_year, student__school=user.school
        )
        task = CourseTaskFactory(course__grade_levels=[enrollment.grade_level])
        week = Week(next_school_year.start_date)

        with self.login(user):
            self.get(
                "core:weekly",
                year=week.first_day.year,
                month=week.first_day.month,
                day=week.first_day.day,
            )

        schedule = self.get_context("schedules")[0]
        assert schedule
        schedule = self.get_context("next_year_schedules")[0]
        course_day = {}
        for course_schedule_item in schedule["courses"][0]["days"]:
            if course_schedule_item["week_date"] == next_school_year.start_date:
                course_day = course_schedule_item
        assert course_day["task"] == task

    def test_show_whats_new_in_context(self):
        """The show_whats_new boolean is in the context."""
        user = self.make_user()
        SchoolYearFactory(school=user.school)
        StudentFactory(school=user.school)
        NotificationFactory(user=user)

        with self.login(user):
            self.get_check_200("core:app")

        assert self.get_context("show_whats_new")

    def test_show_whats_new_does_not_want_announcements(self):
        """The show_whats_new is False for users that don't want announcements."""
        user = self.make_user()
        SchoolYearFactory(school=user.school)
        StudentFactory(school=user.school)
        user.profile.wants_announcements = False
        user.profile.save()
        NotificationFactory(user=user)

        with self.login(user):
            self.get_check_200("core:app")

        assert not self.get_context("show_whats_new")

    def test_show_whats_new_no_unread_notifications(self):
        """The show_whats_new is False when there are no unread notifications."""
        user = self.make_user()
        SchoolYearFactory(school=user.school)
        StudentFactory(school=user.school)
        NotificationFactory(user=user, status=Notification.NotificationStatus.VIEWED)

        with self.login(user):
            self.get_check_200("core:app")

        assert not self.get_context("show_whats_new")

    def test_no_school_years(self):
        """When no school years exist, it is marked in the context."""
        user = self.make_user()
        # Other user's school years don't count.
        SchoolYearFactory()

        with self.login(user):
            self.get_check_200("core:app")

        assert not self.get_context("has_school_years")

    def test_no_students(self):
        """When no student exists, it is marked in the context."""
        user = self.make_user()
        # Other user's students don't count.
        StudentFactory()

        with self.login(user):
            self.get_check_200("core:app")

        assert not self.get_context("has_students")

    def test_no_students_with_task(self):
        """Even when no student exists, the start banner may appear."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        CourseTaskFactory(course__grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("core:app")

        assert not self.get_context("has_students")
        assert self.get_context("has_tasks")


class TestDaily(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:daily")

    def test_ok(self):
        user = self.make_user()
        today = timezone.localdate()
        SchoolYearFactory(school=user.school)
        StudentFactory(school=user.school)

        with self.login(user):
            self.get_check_200("core:daily")

        assert self.get_context("day") == today
        first_day = Week(today).first_day
        assert self.get_context("weekly_url") == self.reverse(
            "core:weekly", first_day.year, first_day.month, first_day.day
        )

    def test_no_school_years(self):
        """When no school years exist, it is marked in the context."""
        user = self.make_user()
        # Other user's school years don't count.
        SchoolYearFactory()

        with self.login(user):
            self.get_check_200("core:daily")

        assert not self.get_context("has_school_years")

    @mock.patch("homeschool.users.models.timezone")
    def test_school_not_run_on_day(self, mock_timezone):
        sunday = timezone.localdate() + relativedelta(weekday=SU)
        mock_timezone.localdate.return_value = sunday
        user = self.make_user()
        SchoolYearFactory(school=user.school, days_of_week=SchoolYear.MONDAY)
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:daily")

        self.assertContext("schedules", [])

    @mock.patch("homeschool.users.models.timezone")
    def test_school_year_for_user_only(self, mock_timezone):
        """A user may only access their school year."""
        friday = timezone.localdate() + relativedelta(weekday=FR)
        mock_timezone.localdate.return_value = friday
        user = self.make_user()
        SchoolYearFactory()
        school_year = SchoolYearFactory(school=user.school)
        EnrollmentFactory(
            grade_level__school_year=school_year, student__school=user.school
        )

        with self.login(user):
            self.get("core:daily")

        schedules = self.get_context("schedules")
        assert schedules != []

    @mock.patch("homeschool.users.models.timezone")
    def test_has_schedules(self, mock_timezone):
        friday = timezone.localdate() + relativedelta(weekday=FR)
        mock_timezone.localdate.return_value = friday
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(
            school=user.school, days_of_week=SchoolYear.FRIDAY
        )
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(grade_levels=[grade_level], days_of_week=Course.FRIDAY)
        task_1 = CourseTaskFactory(course=course)
        coursework = CourseworkFactory(
            student=student, course_task=task_1, completed_date=friday
        )
        course_2 = CourseFactory(grade_levels=[grade_level], days_of_week=Course.FRIDAY)
        task_2a = CourseTaskFactory(course=course_2)
        CourseworkFactory(
            student=student,
            course_task=task_2a,
            completed_date=friday - datetime.timedelta(days=1),
        )
        task_2b = CourseTaskFactory(course=course_2)
        course_3 = CourseFactory(
            grade_levels=[grade_level], days_of_week=Course.THURSDAY
        )
        CourseTaskFactory(course=course_3)
        course_4 = CourseFactory(grade_levels=[grade_level], days_of_week=Course.FRIDAY)
        EnrollmentFactory(student=student, grade_level=grade_level)

        with self.login(user):
            self.get("core:daily")

        expected_schedule = {
            "student": student,
            "courses": [
                {"course": course, "coursework": [coursework]},
                {"course": course_2, "task": task_2b},
                {"course": course_3},
                {"course": course_4, "no_scheduled_task": True},
            ],
        }
        self.assertContext("schedules", [expected_schedule])

    @mock.patch("homeschool.users.models.timezone")
    def test_no_scheduled_task_for_course(self, mock_timezone):
        """A course scheduled to run for a day that has no task messages the user."""
        now = timezone.now()
        monday = now.date() + relativedelta(weekday=MO(-1))
        mock_timezone.localdate.return_value = monday
        user = self.make_user()
        enrollment = EnrollmentFactory(
            grade_level__school_year__school=user.school, student__school=user.school
        )
        course = CourseFactory(grade_levels=[enrollment.grade_level])

        with self.login(user):
            self.get("core:daily")

        expected_schedule = {"course": course, "no_scheduled_task": True}
        assert self.get_context("schedules")[0]["courses"][0] == expected_schedule

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
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(grade_levels=[grade_level])
        CourseworkFactory(
            student=student,
            course_task__course=course,
            completed_date=thursday - datetime.timedelta(days=1),
        )
        CourseTaskFactory(course=course)  # current task for thursday
        CourseTaskFactory(course=course)  # projected task for friday
        task = CourseTaskFactory(course=course)
        EnrollmentFactory(student=student, grade_level=grade_level)

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
        SchoolYearFactory(school=user.school)
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:daily_for_date", year=day.year, month=day.month, day=day.day)

        self.assertContext("day", day)

    def test_surrounding_dates_no_current_school_year(self):
        """When there is no current school year, pull the dates from today."""
        user = self.make_user()
        today = timezone.localdate()
        SchoolYearFactory(
            school=user.school,
            start_date=today - datetime.timedelta(days=5),
            end_date=today - datetime.timedelta(days=1),
        )
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:daily")

        self.assertContext("ereyesterday", today - datetime.timedelta(days=2))
        self.assertContext("yesterday", today - datetime.timedelta(days=1))
        self.assertContext("tomorrow", today + datetime.timedelta(days=1))
        self.assertContext("overmorrow", today + datetime.timedelta(days=2))

    @mock.patch("homeschool.users.models.timezone")
    def test_surrounding_dates(self, mock_timezone):
        wednesday = timezone.localdate() + relativedelta(weekday=WE)
        mock_timezone.localdate.return_value = wednesday
        user = self.make_user()
        SchoolYearFactory(
            school=user.school,
            days_of_week=SchoolYear.TUESDAY
            + SchoolYear.WEDNESDAY
            + SchoolYear.THURSDAY,
        )
        StudentFactory(school=user.school)

        with self.login(user):
            self.get("core:daily")

        previous_thursday = wednesday - datetime.timedelta(days=6)
        self.assertContext("ereyesterday", previous_thursday)
        self.assertContext("yesterday", wednesday - datetime.timedelta(days=1))
        self.assertContext("tomorrow", wednesday + datetime.timedelta(days=1))
        next_tuesday = wednesday + datetime.timedelta(days=6)
        self.assertContext("overmorrow", next_tuesday)

    @mock.patch("homeschool.users.models.timezone")
    def test_schedules_in_grade_level_order(self, mock_timezone):
        """The schedules are in the same order as the grade levels."""
        wednesday = timezone.localdate() + relativedelta(weekday=WE)
        mock_timezone.localdate.return_value = wednesday
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year=school_year)
        grade_level_2 = GradeLevelFactory(school_year=school_year)
        enrollment = EnrollmentFactory(
            grade_level=grade_level_2, student__school=user.school
        )
        enrollment_2 = EnrollmentFactory(
            grade_level=grade_level, student__school=user.school
        )

        with self.login(user):
            self.get("core:daily")

        schedules = self.get_context("schedules")
        assert schedules[0]["student"] == enrollment_2.student
        assert schedules[1]["student"] == enrollment.student

    def test_complete_daily(self):
        today = timezone.now().date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        task = CourseTaskFactory(course__grade_levels=[grade_level])
        data = {
            "completed_date": "{:%Y-%m-%d}".format(today),
            f"task-{student.id}-{task.id}": "on",
        }

        with self.login(user):
            self.post("core:daily", data=data)

        assert Coursework.objects.filter(
            student=student, course_task=task, completed_date=today
        ).exists()

    def test_incomplete_daily(self):
        today = timezone.now().date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        task = CourseTaskFactory(course__grade_levels=[grade_level])
        CourseworkFactory(student=student, course_task=task)
        data = {
            "completed_date": "{:%Y-%m-%d}".format(today),
            f"task-{student.id}-{task.id}": "off",
        }

        with self.login(user):
            self.post("core:daily", data=data)

        assert not Coursework.objects.filter(student=student, course_task=task).exists()

    def test_to_grade(self):
        today = timezone.now().date()
        user = self.make_user()
        student = StudentFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year__school=user.school)
        graded_work = GradedWorkFactory(course_task__course__grade_levels=[grade_level])
        data = {
            "completed_date": "{:%Y-%m-%d}".format(today),
            f"task-{student.id}-{graded_work.course_task.id}": "on",
        }

        with self.login(user):
            response = self.post("core:daily", data=data)

        self.response_302(response)
        url = self.reverse("students:grade")
        assert url in response.get("Location")

    def test_no_grade_when_already_graded(self):
        today = timezone.now().date()
        user = self.make_user()
        school = user.school
        student = StudentFactory(school=school)
        grade_level = GradeLevelFactory(school_year__school=school)
        grade = GradeFactory(
            student=student,
            graded_work__course_task__course__grade_levels=[grade_level],
        )
        data = {
            "completed_date": "{:%Y-%m-%d}".format(today),
            f"task-{student.id}-{grade.graded_work.course_task.id}": "on",
        }

        with self.login(user):
            response = self.post("core:daily", data=data)

        self.response_302(response)
        assert response.get("Location") == self.reverse("core:daily")

    def test_future_school_year(self):
        """A future school year displays the expected task on a day."""
        today = timezone.localdate()
        user = self.make_user()
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + relativedelta(years=1, month=1, day=1),
            end_date=today + relativedelta(years=1, month=12, day=31),
            days_of_week=SchoolYear.ALL_DAYS,
        )
        enrollment = EnrollmentFactory(
            grade_level__school_year=school_year, student__school=user.school
        )
        task = CourseTaskFactory(course__grade_levels=[enrollment.grade_level])

        with self.login(user):
            self.get(
                "core:daily_for_date",
                year=school_year.start_date.year,
                month=school_year.start_date.month,
                day=school_year.start_date.day,
            )

        schedule = self.get_context("schedules")[0]
        assert schedule["courses"][0].get("task") == task

    def test_break_day(self):
        """A break day is noted in the context and nothing is scheduled."""
        today = timezone.localdate()
        user = self.make_user()
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + relativedelta(month=1, day=1),
            end_date=today + relativedelta(month=12, day=31),
            days_of_week=SchoolYear.ALL_DAYS,
        )
        SchoolBreakFactory(
            school_year=school_year,
            start_date=school_year.start_date,
            end_date=school_year.end_date,
        )
        enrollment = EnrollmentFactory(
            grade_level__school_year=school_year, student__school=user.school
        )
        CourseTaskFactory(course__grade_levels=[enrollment.grade_level])

        with self.login(user):
            self.get(
                "core:daily_for_date",
                year=school_year.start_date.year,
                month=school_year.start_date.month,
                day=school_year.start_date.day,
            )

        assert self.get_context("is_break_day")
        assert self.get_context("schedules") == []

    def test_no_students(self):
        """When no student exists, it is marked in the context."""
        user = self.make_user()
        # Other user's students don't count.
        StudentFactory()

        with self.login(user):
            self.get_check_200("core:daily")

        assert not self.get_context("has_students")

    def test_no_students_with_task(self):
        """Even when no student exists, the start banner may appear."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        CourseTaskFactory(course__grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("core:daily")

        assert not self.get_context("has_students")
        assert self.get_context("has_tasks")


class TestStartView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:start")

    def test_ok(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("core:start")

    def test_no_message_on_visit(self):
        """Clear out messages from django-allauth on sign up."""
        user = self.make_user()
        self.client.cookies["messages"] = CookieStorage(request=None)._encode(
            [Message(messages.INFO, "Find me")]
        )

        with self.login(user):
            response = self.get("core:start")

        self.assertResponseNotContains("Find me", response)
        assert response.cookies["messages"].value == ""


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

        school_year = SchoolYear.objects.get(school=user.school)
        assert school_year.days_of_week == (
            SchoolYear.MONDAY
            + SchoolYear.TUESDAY
            + SchoolYear.WEDNESDAY
            + SchoolYear.THURSDAY
            + SchoolYear.FRIDAY
        )
        self.response_302(response)
        assert response.get("Location") == self.reverse("core:start-grade-level")

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
        assert form.non_field_errors() == [
            "The start date must be before the end date."
        ]

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
        assert form.non_field_errors() == [
            "A school year cannot be created for a different school."
        ]

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
        assert response.get("Location") == self.reverse("core:start-course")

    def test_only_school_year_for_user(self):
        user = self.make_user()
        school_year = SchoolYearFactory()
        data = {"school_year": str(school_year.id), "name": "Kindergarten"}

        with self.login(user):
            response = self.post("core:start-grade-level", data=data)

        self.response_200(response)
        form = self.get_context("form")
        assert form.non_field_errors() == [
            "A grade level cannot be created for a different user's school year."
        ]

    def test_bogus_school_year(self):
        user = self.make_user()
        data = {"school_year": "0", "name": "Kindergarten"}

        with self.login(user):
            response = self.post("core:start-grade-level", data=data)

        self.response_200(response)
        form = self.get_context("form")
        assert form.non_field_errors() == ["Invalid school year."]


class TestStartCourseView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:start-course")

    def test_ok(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("core:start-course")

        assert self.get_context("grade_level") == grade_level
        assert self.get_context("course") == course

    def test_only_users_grade_level(self):
        """The grade level must belong to the user."""
        user = self.make_user()
        GradeLevelFactory()

        with self.login(user):
            self.get_check_200("core:start-course")

        assert self.get_context("grade_level") is None

    def test_only_users_course(self):
        """The course must belong to the user for the grade level."""
        user = self.make_user()
        GradeLevelFactory(school_year__school=user.school)
        CourseFactory()

        with self.login(user):
            self.get_check_200("core:start-course")

        assert self.get_context("course") is None

    def test_post(self):
        """A successful POST creates a course."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        data = {
            "name": "Astronomy",
            "default_task_duration": "30",
            "grade_levels": str(grade_level.id),
        }

        with self.login(user):
            response = self.post("core:start-course", data=data)

        assert response.status_code == 302
        assert response["Location"] == self.reverse("core:start-course-task")
        assert Course.objects.filter(name="Astronomy").exists()


class TestStartCourseTaskView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:start-course-task")

    def test_ok(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)

        with self.login(user):
            self.get_check_200("core:start-course-task")

        assert self.get_context("course") == course
        assert self.get_context("task") == task

    def test_only_users_course(self):
        """The course must belong to the user."""
        user = self.make_user()
        CourseFactory()

        with self.login(user):
            self.get_check_200("core:start-course-task")

        assert self.get_context("course") is None

    def test_only_users_course_task(self):
        """The task must belong to the user."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory()

        with self.login(user):
            self.get_check_200("core:start-course-task")

        assert self.get_context("task") is None

    def test_post(self):
        """A successful POST creates a course."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "description": "My first task",
            "duration": str(course.default_task_duration),
            "course": str(course.id),
        }

        with self.login(user):
            response = self.post("core:start-course-task", data=data)

        assert response.status_code == 302
        assert (
            response["Location"]
            == self.reverse("schools:current_school_year") + f"?welcome={course.uuid}"
        )
        assert CourseTask.objects.filter(description="My first task").exists()


class TestBoom(TestCase):
    def test_non_staff(self):
        """A non-staff user cannot trigger the error page."""
        user = self.make_user()

        with self.login(user):
            response = self.get("boom")

        self.response_302(response)

    def test_staff(self):
        """A staff user can trigger the error page."""
        user = UserFactory(is_staff=True)

        with self.login(user), pytest.raises(Exception) as excinfo:
            self.get("boom")

        assert str(excinfo.value) == "Is this thing on?"


class TestHandle500(TestCase):
    def test_get(self):
        response = self.get("handle_500")

        assert response.status_code == 500
