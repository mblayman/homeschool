from homeschool.courses.tests.factories import CourseFactory
from homeschool.schools.models import SchoolYear
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolFactory,
    SchoolYearFactory,
)
from homeschool.test import TestCase


class TestSchool(TestCase):
    def test_factory(self):
        school = SchoolFactory()

        self.assertIsNotNone(school)

    def test_has_admin(self):
        user = self.make_user()
        school = SchoolFactory(admin=user)

        self.assertEqual(school.admin, user)


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

    def test_days_of_week_default(self):
        school_year = SchoolYearFactory()

        self.assertTrue(school_year.runs_on(SchoolYear.MONDAY))
        self.assertTrue(school_year.runs_on(SchoolYear.TUESDAY))
        self.assertTrue(school_year.runs_on(SchoolYear.WEDNESDAY))
        self.assertTrue(school_year.runs_on(SchoolYear.THURSDAY))
        self.assertTrue(school_year.runs_on(SchoolYear.FRIDAY))
        self.assertFalse(school_year.runs_on(SchoolYear.SATURDAY))
        self.assertFalse(school_year.runs_on(SchoolYear.SUNDAY))


class TestGradeLevel(TestCase):
    def test_factory(self):
        grade_level = GradeLevelFactory()

        self.assertIsNotNone(grade_level)
        self.assertNotEqual(grade_level.name, "")

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
        course = CourseFactory(grade_level=grade_level)

        self.assertEqual(list(grade_level.courses.all()), [course])
