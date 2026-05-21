import datetime
from unittest import mock

import pytest
import time_machine
from dateutil.relativedelta import FR, MO, SA, SU, WE, relativedelta
from django.conf import settings
from django.contrib.messages import get_messages
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
    SchoolYearFactory,
)
from homeschool.students.models import Coursework, Enrollment, Student
from homeschool.students.tests.factories import (
    CourseworkFactory,
    EnrollmentFactory,
    GradeFactory,
    StudentFactory,
)
from homeschool.test import TestCase
from homeschool.users.tests.factories import UserFactory


class TestUp(TestCase):
    def test_ok(self):
        self.get_check_200("core:up")


class TestIndex(TestCase):
    def test_ok(self):
        self.get_check_200("core:index")


class TestRobots(TestCase):
    def test_ok(self):
        self.get_check_200("core:robots")


class TestSiteMapIndex(TestCase):
    def test_ok(self):
        self.get_check_200("core:sitemapindex")


class TestSiteMap(TestCase):
    def test_ok(self):
        self.get_check_200("core:sitemap")


class TestAbout(TestCase):
    def test_ok(self):
        self.get_check_200("core:about")


class TestTerms(TestCase):
    def test_ok(self):
        self.get_check_200("core:terms")


class TestPrivacy(TestCase):
    def test_ok(self):
        self.get_check_200("core:privacy")


class TestHelp(TestCase):
    def test_ok(self):
        self.get_check_200("core:help")

        self.assertResponseNotContains(settings.SUPPORT_EMAIL)

    def test_has_support_email(self):
        """The support email is available to authenticated users."""
        user = self.make_user()

        with self.login(user):
            self.get_check_200("core:help")

        self.assertResponseContains(settings.SUPPORT_EMAIL)


class TestBlogRedirect(TestCase):
    def test_blog_root_redirects_home_with_message(self):
        response = self.get("blog-redirect")

        self.response_302(response)
        assert response.get("Location") == self.reverse("core:index")
        message = list(get_messages(response.wsgi_request))[0]
        assert (
            str(message)
            == "The School Desk blog is retired. You were redirected to the home page."
        )

    def test_blog_path_redirects_home_with_message(self):
        response = self.get("/blog/some-old-post/")

        self.response_302(response)
        assert response.get("Location") == self.reverse("core:index")
        message = list(get_messages(response.wsgi_request))[0]
        assert (
            str(message)
            == "The School Desk blog is retired. You were redirected to the home page."
        )


class TestDashboard(TestCase):
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

    def test_redirects_brand_new_user_to_start(self):
        user = self.make_user()

        with self.login(user):
            response = self.get("core:dashboard")

        self.response_302(response)
        assert response["Location"] == self.reverse("core:start")

    def test_allows_started_user(self):
        user = self.make_user()
        SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("core:dashboard")

        assert self.get_context("nav_link") == "dashboard"

    def test_allows_completed_user(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        student = StudentFactory(school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory(course=course)

        with self.login(user):
            self.get_check_200("core:dashboard")

        assert self.get_context("nav_link") == "dashboard"

    def test_allows_partially_started_user(self):
        user = self.make_user()
        SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("core:dashboard")

        assert self.get_context("nav_link") == "dashboard"

    @mock.patch("homeschool.users.models.timezone")
    def test_has_days(self, timezone):
        """The context has the first and last day of the week."""
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=datetime.UTC)
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
            self.get("core:dashboard")

        assert self.get_context("first_day") == first_day
        assert self.get_context("last_day") == last_day

    @mock.patch("homeschool.users.models.timezone")
    def test_has_surrounding_week_dates(self, timezone):
        """The context has the previous and next week dates."""
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=datetime.UTC)
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
            self.get("core:dashboard")

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
            self.get("core:dashboard")

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
            self.get("core:dashboard")

        schedules = self.get_context("schedules")
        assert len(schedules[0]["courses"]) > 0
        assert self.get_context("school_year") == grade_level.school_year

    @mock.patch("homeschool.users.models.timezone")
    def test_has_schedules(self, timezone):
        """The schedules are in the context."""
        now = datetime.datetime(2020, 1, 23, tzinfo=datetime.UTC)
        thursday = now.date()
        monday = thursday - datetime.timedelta(days=3)
        friday = thursday + datetime.timedelta(days=1)
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student, grade_level = self.make_student_enrolled_in_grade_level(user, thursday)
        course = CourseFactory(
            grade_levels=[grade_level],
            days_of_week=Course.MONDAY
            + Course.WEDNESDAY
            + Course.THURSDAY
            + Course.FRIDAY,
        )
        task_1 = CourseTaskFactory(course=course)
        task_2 = CourseTaskFactory(course=course)
        coursework = CourseworkFactory(
            student=student, course_task=task_1, completed_date=monday
        )
        school_break = SchoolBreakFactory(
            school_year=grade_level.school_year, start_date=friday, end_date=friday
        )

        with self.login(user), self.assertNumQueries(19):
            self.get("core:dashboard")

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
                            "school_break": None,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=3),
                            "task": task_2,
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
            "week_dates": [
                {"date": monday, "school_break": None},
                {"date": monday + datetime.timedelta(days=1), "school_break": None},
                {"date": monday + datetime.timedelta(days=2), "school_break": None},
                {"date": monday + datetime.timedelta(days=3), "school_break": None},
                {
                    "date": monday + datetime.timedelta(days=4),
                    "date_type": SchoolBreak.DateType.SINGLE,
                    "school_break": school_break,
                },
            ],
        }
        schedules = self.get_context("schedules")
        assert schedules == [expected_schedule]

    @mock.patch("homeschool.users.models.timezone")
    def test_weekly(self, timezone):
        """The weekly schedule is available in the context."""
        now = datetime.datetime(2020, 1, 24, tzinfo=datetime.UTC)  # A Friday
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
        CourseworkFactory(student=student, course_task=task_1, completed_date=monday)
        # Because this is a Friday, this task would appear on the current week.
        CourseTaskFactory(course=course)
        # But these tasks would roll forward to next week's view
        # and appear on the expected schedule.
        task_2 = CourseTaskFactory(course=course)
        task_3 = CourseTaskFactory(course=course)
        task_4 = CourseTaskFactory(course=course)

        with self.login(user), self.assertNumQueries(20):
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
                            "task": task_3,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=10),
                            "school_break": None,
                            "task": task_4,
                        },
                        {
                            "week_date": monday + datetime.timedelta(days=11),
                            "school_break": None,
                        },
                    ],
                }
            ],
            "week_dates": [
                {"date": monday + datetime.timedelta(days=7), "school_break": None},
                {"date": monday + datetime.timedelta(days=8), "school_break": None},
                {"date": monday + datetime.timedelta(days=9), "school_break": None},
                {"date": monday + datetime.timedelta(days=10), "school_break": None},
                {"date": monday + datetime.timedelta(days=11), "school_break": None},
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
        now = datetime.datetime(2020, 1, 26, tzinfo=datetime.UTC)
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
        now = datetime.datetime(2020, 1, 23, tzinfo=datetime.UTC)
        thursday = now.date()
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student, grade_level = self.make_student_enrolled_in_grade_level(user, thursday)
        course = CourseFactory(grade_levels=[grade_level], days_of_week=Course.NO_DAYS)
        CourseTaskFactory(course=course)

        with self.login(user):
            self.get("core:dashboard")

        schedules = self.get_context("schedules")
        assert schedules[0]["courses"] == []

    @mock.patch("homeschool.users.models.timezone")
    def test_show_course_when_no_days_in_past(self, timezone):
        """When the week is in the past, show the course, even if it's not running."""
        now = datetime.datetime(2020, 1, 25, tzinfo=datetime.UTC)
        saturday = now.date()
        timezone.localdate.return_value = now.date()
        user = self.make_user()
        student, grade_level = self.make_student_enrolled_in_grade_level(user, saturday)
        course = CourseFactory(grade_levels=[grade_level], days_of_week=Course.NO_DAYS)
        CourseTaskFactory(course=course)

        with self.login(user):
            self.get("core:dashboard")

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
            self.get("core:dashboard")

        schedules = self.get_context("schedules")
        assert schedules[0]["student"] == enrollment_2.student
        assert schedules[1]["student"] == enrollment.student

    @time_machine.travel("2021-11-28")
    def test_future_school_year(self):
        """A future school year shows the task in a week at the school year start.

        This test setup has a problem where the school year conditions to make
        this line up are annoying. This started failing when the test looked
        ahead to 2023 when the week start perfectly lined up with 1/1
        which is the same date as the school year start. This caused the "future"
        school year to look like a current school year. Freeze time to make
        the test conditions right.
        """
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
        task = CourseTaskFactory(
            course__grade_levels=[enrollment.grade_level],
            course__days_of_week=Course.ALL_DAYS,
        )
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

    @time_machine.travel("2021-11-28")
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
        CourseTaskFactory(
            course__grade_levels=[enrollment.grade_level],
            course__days_of_week=Course.ALL_DAYS,
        )
        next_school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + relativedelta(years=1, month=1, day=1),
            end_date=today + relativedelta(years=1, month=12, day=31),
            days_of_week=SchoolYear.ALL_DAYS,
        )
        enrollment = EnrollmentFactory(
            grade_level__school_year=next_school_year, student__school=user.school
        )
        task = CourseTaskFactory(
            course__grade_levels=[enrollment.grade_level],
            course__days_of_week=Course.ALL_DAYS,
        )
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
            self.get_check_200("core:dashboard")

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
            self.get_check_200("core:dashboard")

        assert not self.get_context("show_whats_new")

    def test_show_whats_new_no_unread_notifications(self):
        """The show_whats_new is False when there are no unread notifications."""
        user = self.make_user()
        SchoolYearFactory(school=user.school)
        StudentFactory(school=user.school)
        NotificationFactory(user=user, status=Notification.NotificationStatus.VIEWED)

        with self.login(user):
            self.get_check_200("core:dashboard")

        assert not self.get_context("show_whats_new")

    def test_no_students(self):
        """When no student exists, it is marked in the context."""
        user = self.make_user()
        SchoolYearFactory(school=user.school)
        # Other user's students don't count.
        StudentFactory()

        with self.login(user):
            self.get_check_200("core:dashboard")

        assert not self.get_context("has_students")

    def test_no_students_with_task(self):
        """Even when no student exists, the start banner may appear."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        CourseTaskFactory(course__grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("core:dashboard")

        assert not self.get_context("has_students")
        assert self.get_context("has_tasks")

    @mock.patch("homeschool.users.models.timezone")
    def test_future_school_year_cta(self, mock_timezone):
        """When on a week with no schedule, the future school CTA is present."""
        sunday = timezone.localdate() + relativedelta(weekday=SU)
        mock_timezone.localdate.return_value = sunday
        user = self.make_user()
        StudentFactory(school=user.school)
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=sunday + datetime.timedelta(90),
            end_date=sunday + datetime.timedelta(290),
            days_of_week=SchoolYear.ALL_DAYS,
        )

        with self.login(user):
            self.get("core:dashboard")

        assert self.get_context("future_school_year") == school_year
        start = Week(school_year.start_date).first_day
        url = self.reverse("core:weekly", start.year, start.month, start.day)
        assert self.get_context("future_school_year_week_url") == url


class TestDaily(TestCase):
    def test_ok(self):
        user = self.make_user()
        today = timezone.localdate()
        SchoolYearFactory(school=user.school)
        StudentFactory(school=user.school)

        with self.login(user):
            self.get_check_200("core:daily")

        assert self.get_context("nav_link") == "daily"
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
            "is_break": False,
        }
        self.assertContext("schedules", [expected_schedule])

    @mock.patch("homeschool.users.models.timezone")
    def test_is_break_for_student(self, mock_timezone):
        """A student's break day appears in the schedule."""
        friday = timezone.localdate() + relativedelta(weekday=FR)
        mock_timezone.localdate.return_value = friday
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(
            school=user.school, days_of_week=SchoolYear.FRIDAY
        )
        grade_level = GradeLevelFactory(school_year=school_year)
        EnrollmentFactory(student=student, grade_level=grade_level)
        other_enrollment = EnrollmentFactory(grade_level=grade_level)
        school_break = SchoolBreakFactory(
            start_date=friday, end_date=friday, school_year=school_year
        )
        school_break.students.add(student)

        with self.login(user):
            self.get("core:daily")

        assert self.get_context("schedules") == [
            {"student": student, "courses": [], "is_break": True},
            {"student": other_enrollment.student, "courses": [], "is_break": False},
        ]

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
        now = datetime.datetime(2020, 1, 23, tzinfo=datetime.UTC)
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
            "is_break": False,
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
            "completed_date": f"{today:%Y-%m-%d}",
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
            "completed_date": f"{today:%Y-%m-%d}",
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
            "completed_date": f"{today:%Y-%m-%d}",
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
            "completed_date": f"{today:%Y-%m-%d}",
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
        task = CourseTaskFactory(
            course__grade_levels=[enrollment.grade_level],
            course__days_of_week=Course.ALL_DAYS,
        )

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


class TestStartSetupView(TestCase):
    def test_ok(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("core:start")

    def test_school_year_placeholders_follow_the_calendar(self):
        user = self.make_user()

        cases = [
            (
                datetime.date(2026, 5, 20),
                "9/1/2026",
                "6/1/2027",
            ),
            (
                datetime.date(2026, 10, 15),
                "9/1/2027",
                "6/1/2028",
            ),
        ]

        for today, start_placeholder, end_placeholder in cases:
            with self.subTest(today=today):
                with (
                    self.login(user),
                    mock.patch(
                        "homeschool.core.views.timezone", autospec=True
                    ) as mock_timezone,
                ):
                    mock_timezone.localdate.return_value = today
                    response = self.get("core:start")

                self.response_200(response)
                html = response.content.decode()
                assert f'placeholder="{start_placeholder}"' in html
                assert f'placeholder="{end_placeholder}"' in html

    def test_partially_started_user_redirects_to_dashboard(self):
        user = self.make_user()
        SchoolYearFactory(school=user.school)

        with self.login(user):
            response = self.get("core:start")

        self.response_302(response)
        assert response["Location"] == self.reverse("core:dashboard")

    def test_completed_user_redirects_to_dashboard(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year=school_year)
        student = StudentFactory(school=user.school)
        EnrollmentFactory(student=student, grade_level=grade_level)
        course = CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory(course=course)

        with self.login(user):
            response = self.get("core:start")

        self.response_302(response)
        assert response["Location"] == self.reverse("core:dashboard")

    def test_post_creates_starting_data(self):
        user = self.make_user()
        data = {
            "school_year_start_date": "1/1/20",
            "school_year_end_date": "12/31/20",
            "grade_level_name": "Kindergarten",
            "student_first_name": "Ada",
            "student_last_name": "Lovelace",
            "course_name": "Math",
            "course_task_description": "Read chapter 1",
        }

        with self.login(user):
            response = self.post("core:start", data=data)

        school_year = SchoolYear.objects.get(school=user.school)
        grade_level = GradeLevel.objects.get(school_year=school_year)
        student = Student.objects.get(school=user.school)
        course = Course.objects.get(grade_levels=grade_level)
        course_task = CourseTask.objects.get(course=course)
        enrollment = Enrollment.objects.get(student=student, grade_level=grade_level)
        assert school_year.start_date == datetime.date(2020, 1, 1)
        assert school_year.end_date == datetime.date(2020, 12, 31)
        assert grade_level.name == "Kindergarten"
        assert student.first_name == "Ada"
        assert student.last_name == "Lovelace"
        assert course.name == "Math"
        assert course_task.description == "Read chapter 1"
        assert enrollment is not None
        self.response_302(response)
        assert (
            response["Location"]
            == self.reverse("schools:current_school_year") + f"?welcome={course.id}"
        )

    def test_start_date_before_end_date(self):
        user = self.make_user()
        data = {
            "school_year_start_date": "12/31/20",
            "school_year_end_date": "1/1/20",
            "grade_level_name": "Kindergarten",
            "student_first_name": "Ada",
            "student_last_name": "Lovelace",
            "course_name": "Math",
            "course_task_description": "Read chapter 1",
        }

        with self.login(user):
            response = self.post("core:start", data=data)

        self.response_200(response)
        form = self.get_context("form")
        assert form.non_field_errors() == [
            "The start date must be before the end date."
        ]

    def test_school_year_max_length(self):
        user = self.make_user()
        data = {
            "school_year_start_date": "1/1/20",
            "school_year_end_date": "12/31/22",
            "grade_level_name": "Kindergarten",
            "student_first_name": "Ada",
            "student_last_name": "Lovelace",
            "course_name": "Math",
            "course_task_description": "Read chapter 1",
        }

        with self.login(user):
            response = self.post("core:start", data=data)

        self.response_200(response)
        form = self.get_context("form")
        assert form.non_field_errors() == [
            "A school year may not be longer than 500 days."
        ]


class TestOfficeDashboard(TestCase):
    def test_staff(self):
        """A staff user can access the page."""
        user = UserFactory(is_staff=True)

        with self.login(user):
            self.get_check_200("office:dashboard")


class TestOfficeOnboarding(TestCase):
    def test_staff(self):
        """A staff user can access the page."""
        user = UserFactory(is_staff=True)

        with self.login(user):
            self.get_check_200("office:onboarding")

    def test_marks_tirekicker(self):
        """A tirekicker that is not using the app is marked for the context."""
        tirekicker_cutoff = timezone.now() - datetime.timedelta(days=8)
        user = UserFactory(is_staff=True)
        enrollment = EnrollmentFactory(
            grade_level__school_year__school__admin__date_joined=tirekicker_cutoff
        )
        CourseTaskFactory(course__grade_levels=[enrollment.grade_level])

        with self.login(user):
            self.get_check_200("office:onboarding")

        assert self.get_context("tirekicker_count") == 1


class TestBoom(TestCase):
    def test_staff(self):
        """A staff user can trigger the error page."""
        user = UserFactory(is_staff=True)

        with self.login(user), pytest.raises(Exception) as excinfo:
            self.get("office:boom")

        assert str(excinfo.value) == "Is this thing on?"


class TestSocialImage(TestCase):
    def test_staff(self):
        """A staff user can access the page."""
        user = UserFactory(is_staff=True)

        with self.login(user):
            self.get_check_200("office:social_image")


class TestHandle403(TestCase):
    def test_get(self):
        response = self.get("office:handle_403")

        assert response.status_code == 403
        assert "Forbidden" in response.content.decode()


class TestHandle404(TestCase):
    def test_get(self):
        response = self.get("office:handle_404")

        assert response.status_code == 404
        assert "Not Found" in response.content.decode()


class TestHandle500(TestCase):
    def test_get(self):
        response = self.get("office:handle_500")

        assert response.status_code == 500


class TestFavicon(TestCase):
    def test_get(self):
        response = self.get("favicon")

        assert response.status_code == 301
        assert response["Location"] == "/static/favicon/favicon.ico"
