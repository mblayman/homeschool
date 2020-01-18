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
