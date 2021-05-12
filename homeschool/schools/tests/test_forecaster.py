import datetime

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from freezegun import freeze_time

from homeschool.courses.models import Course
from homeschool.courses.tests.factories import CourseFactory, CourseTaskFactory
from homeschool.schools.forecaster import Forecaster
from homeschool.schools.models import SchoolYear
from homeschool.schools.tests.factories import SchoolYearFactory
from homeschool.students.tests.factories import CourseworkFactory, EnrollmentFactory
from homeschool.test import TestCase


class TestForecaster(TestCase):
    @freeze_time("2021-03-10")  # Wednesday
    def test_get_last_forecast_date(self):
        """The forecast returns the final projected date of a course."""
        enrollment = EnrollmentFactory()
        student = enrollment.student
        course = CourseFactory(grade_levels=[enrollment.grade_level])
        CourseTaskFactory(course=course)
        CourseTaskFactory(course=course)
        forecaster = Forecaster()
        expected_last_date = datetime.date(2021, 3, 11)

        last_date = forecaster.get_last_forecast_date(student, course)

        assert last_date == expected_last_date

    def test_no_tasks_to_forecast(self):
        """No tasks returns a last date of None."""
        enrollment = EnrollmentFactory()
        student = enrollment.student
        course = CourseFactory(grade_levels=[enrollment.grade_level])
        forecaster = Forecaster()

        last_date = forecaster.get_last_forecast_date(student, course)

        assert last_date is None

    @freeze_time("2021-03-10")  # Wednesday
    def test_all_tasks_completed(self):
        """The last date matched the coursework completion."""
        enrollment = EnrollmentFactory()
        student = enrollment.student
        course = CourseFactory(grade_levels=[enrollment.grade_level])
        task = CourseTaskFactory(course=course)
        coursework = CourseworkFactory(student=student, course_task=task)
        forecaster = Forecaster()

        last_date = forecaster.get_last_forecast_date(student, course)

        assert last_date == coursework.completed_date

    @freeze_time("2021-03-10")  # Wednesday
    def test_no_student_forecast(self):
        """The forecaster can produce a forecast for no student."""
        enrollment = EnrollmentFactory()
        course = CourseFactory(grade_levels=[enrollment.grade_level])
        task = CourseTaskFactory(course=course)
        forecaster = Forecaster()

        items = forecaster.get_items_by_task(None, course)

        assert items[task]["planned_date"] == datetime.date.today()

    def test_planned_dates_for_future_school_years(self):
        """The planned dates for a future school year match with the year."""
        today = timezone.localdate()
        user = self.make_user()
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + relativedelta(years=1, month=1, day=1),
            end_date=today + relativedelta(years=1, month=12, day=31),
            days_of_week=SchoolYear.ALL_DAYS,
        )
        enrollment = EnrollmentFactory(
            student__school=user.school, grade_level__school_year=school_year
        )
        course = CourseFactory(
            grade_levels=[enrollment.grade_level], days_of_week=Course.ALL_DAYS
        )
        CourseTaskFactory(course=course)
        forecaster = Forecaster()

        items = forecaster.get_task_items(enrollment.student, course)

        task_item = items[0]
        assert task_item["planned_date"] == school_year.start_date

    def test_no_forecast_course_not_running(self):
        """A course that isn't running will not forecast dates."""
        today = timezone.localdate()
        user = self.make_user()
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + relativedelta(years=1, month=1, day=1),
            end_date=today + relativedelta(years=1, month=12, day=31),
            days_of_week=SchoolYear.ALL_DAYS,
        )
        enrollment = EnrollmentFactory(
            student__school=user.school, grade_level__school_year=school_year
        )
        course = CourseFactory(
            grade_levels=[enrollment.grade_level], days_of_week=Course.NO_DAYS
        )
        CourseTaskFactory(course=course)
        forecaster = Forecaster()

        items = forecaster.get_task_items(enrollment.student, course)

        task_item = items[0]
        assert "planned_date" not in task_item
