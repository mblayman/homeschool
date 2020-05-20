import datetime

from dateutil.relativedelta import MO, relativedelta

from homeschool.core.schedules import Week
from homeschool.courses.tests.factories import CourseFactory
from homeschool.schools.models import SchoolYear
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolFactory,
    SchoolYearFactory,
)
from homeschool.students.tests.factories import StudentFactory
from homeschool.test import TestCase


class TestSchool(TestCase):
    def test_factory(self):
        school = SchoolFactory()

        self.assertIsNotNone(school)

    def test_has_admin(self):
        user = self.make_user()
        school = SchoolFactory(admin=user)

        self.assertEqual(school.admin, user)

    def test_has_students(self):
        school = SchoolFactory()
        student = StudentFactory(school=school)

        self.assertEqual(list(school.students.all()), [student])


class TestSchoolYear(TestCase):
    def test_factory(self):
        school_year = SchoolYearFactory()

        self.assertIsNotNone(school_year)
        self.assertIsNotNone(school_year.start_date)
        self.assertIsNotNone(school_year.end_date)

    def test_has_school(self):
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)

        self.assertEqual(school_year.school, school)

    def test_has_days_of_week(self):
        days_of_week = SchoolYear.MONDAY + SchoolYear.TUESDAY
        school_year = SchoolYearFactory(days_of_week=days_of_week)

        self.assertEqual(school_year.days_of_week, days_of_week)

    def test_has_grade_levels(self):
        school_year = SchoolYearFactory()
        grade_level = GradeLevelFactory(school_year=school_year)

        self.assertEqual(list(school_year.grade_levels.all()), [grade_level])

    def test_runs_on(self):
        school_year = SchoolYearFactory(days_of_week=SchoolYear.MONDAY)

        self.assertTrue(school_year.runs_on(SchoolYear.MONDAY))
        self.assertFalse(school_year.runs_on(SchoolYear.TUESDAY))

    def test_runs_on_date(self):
        school_year = SchoolYearFactory(days_of_week=SchoolYear.MONDAY)
        monday = datetime.date(2020, 1, 20)
        tuesday = datetime.date(2020, 1, 21)

        self.assertTrue(school_year.runs_on(monday))
        self.assertFalse(school_year.runs_on(tuesday))

    def test_get_previous_day_from(self):
        school_year = SchoolYearFactory(days_of_week=SchoolYear.MONDAY)
        monday = datetime.date(2020, 1, 20)
        previous_monday = datetime.date(2020, 1, 13)

        self.assertEqual(school_year.get_previous_day_from(monday), previous_monday)

    def test_get_previous_day_from_no_running_days(self):
        school_year = SchoolYearFactory(days_of_week=0)
        monday = datetime.date(2020, 1, 20)

        self.assertEqual(school_year.get_previous_day_from(monday), monday)

    def test_get_next_day_from(self):
        school_year = SchoolYearFactory(days_of_week=SchoolYear.MONDAY)
        monday = datetime.date(2020, 1, 20)
        next_monday = datetime.date(2020, 1, 27)

        self.assertEqual(school_year.get_next_day_from(monday), next_monday)

    def test_get_next_day_from_no_running_days(self):
        school_year = SchoolYearFactory(days_of_week=0)
        monday = datetime.date(2020, 1, 20)

        self.assertEqual(school_year.get_next_day_from(monday), monday)

    def test_days_of_week_default(self):
        school_year = SchoolYearFactory()

        self.assertTrue(school_year.runs_on(SchoolYear.MONDAY))
        self.assertTrue(school_year.runs_on(SchoolYear.TUESDAY))
        self.assertTrue(school_year.runs_on(SchoolYear.WEDNESDAY))
        self.assertTrue(school_year.runs_on(SchoolYear.THURSDAY))
        self.assertTrue(school_year.runs_on(SchoolYear.FRIDAY))
        self.assertFalse(school_year.runs_on(SchoolYear.SATURDAY))
        self.assertFalse(school_year.runs_on(SchoolYear.SUNDAY))

    def test_get_week_dates_for(self):
        school_year = SchoolYearFactory()
        week = Week(datetime.date(2020, 1, 20))

        self.assertEqual(
            school_year.get_week_dates_for(week),
            [
                datetime.date(2020, 1, 20),
                datetime.date(2020, 1, 21),
                datetime.date(2020, 1, 22),
                datetime.date(2020, 1, 23),
                datetime.date(2020, 1, 24),
            ],
        )

    def test_last_school_day_for_week(self):
        school_year = SchoolYearFactory()
        monday = datetime.date.today() + relativedelta(weekday=MO(-1))
        friday = monday + datetime.timedelta(days=4)
        week = Week(monday)

        last_school_day = school_year.last_school_day_for(week)

        self.assertEqual(last_school_day, friday)

    def test_last_school_day_for_no_days(self):
        school_year = SchoolYearFactory(days_of_week=SchoolYear.NO_DAYS)
        monday = datetime.date.today() + relativedelta(weekday=MO(-1))
        week = Week(monday)

        last_school_day = school_year.last_school_day_for(week)

        self.assertEqual(last_school_day, monday)


class TestGradeLevel(TestCase):
    def test_factory(self):
        grade_level = GradeLevelFactory()

        self.assertIsNotNone(grade_level)
        self.assertNotEqual(grade_level.name, "")

    def test_str(self):
        grade_level = GradeLevelFactory()

        self.assertEqual(str(grade_level), grade_level.name)

    def test_has_name(self):
        name = "Kindergarten"
        grade_level = GradeLevelFactory(name=name)

        self.assertEqual(grade_level.name, name)

    def test_has_school_year(self):
        school_year = SchoolYearFactory()
        grade_level = GradeLevelFactory(school_year=school_year)

        self.assertEqual(grade_level.school_year, school_year)

    def test_has_courses(self):
        grade_level = GradeLevelFactory()
        course = CourseFactory()
        grade_level.courses.add(course)

        self.assertEqual(list(grade_level.courses.all()), [course])
