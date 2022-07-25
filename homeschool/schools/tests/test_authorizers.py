from homeschool.schools.authorizers import school_year_authorized
from homeschool.schools.tests.factories import SchoolYearFactory
from homeschool.test import TestCase


class TestSchoolYearAuthorized(TestCase):
    def test_permitted_course(self):
        """A school year is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        school_year = SchoolYearFactory(school__admin=request.user)

        assert school_year_authorized(request, pk=school_year.pk)

    def test_denied_course(self):
        """Another school year is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        school_year = SchoolYearFactory()

        assert not school_year_authorized(request, pk=school_year.pk)
