import datetime

from freezegun import freeze_time

from homeschool.courses.tests.factories import CourseFactory, CourseTaskFactory
from homeschool.schools.forecaster import Forecaster
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
