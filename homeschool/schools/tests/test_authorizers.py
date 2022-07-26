from homeschool.schools.authorizers import (
    grade_level_authorized,
    school_break_authorized,
    school_year_authorized,
)
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolBreakFactory,
    SchoolYearFactory,
)
from homeschool.test import TestCase


class TestGradeLevelAuthorized(TestCase):
    def test_permitted_grade_level(self):
        """A grade level is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school__admin=request.user)

        assert grade_level_authorized(request, pk=grade_level.pk)

    def test_denied_grade_level(self):
        """Another grade level is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        grade_level = GradeLevelFactory()

        assert not grade_level_authorized(request, pk=grade_level.pk)


class TestSchoolBreakAuthorized(TestCase):
    def test_permitted_school_break(self):
        """A school break is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        school_break = SchoolBreakFactory(school_year__school__admin=request.user)

        assert school_break_authorized(request, pk=school_break.pk)

    def test_denied_school_break(self):
        """Another school break is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        school_break = SchoolBreakFactory()

        assert not school_break_authorized(request, pk=school_break.pk)


class TestSchoolYearAuthorized(TestCase):
    def test_permitted_school_year(self):
        """A school year is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        school_year = SchoolYearFactory(school__admin=request.user)

        assert school_year_authorized(request, pk=school_year.pk)

    def test_denied_school_year(self):
        """Another school year is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        school_year = SchoolYearFactory()

        assert not school_year_authorized(request, pk=school_year.pk)
