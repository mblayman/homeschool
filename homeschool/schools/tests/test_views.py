from homeschool.schools.tests.factories import SchoolYearFactory
from homeschool.test import TestCase


class TestSchoolYearDetailView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("schools:school_year_detail", uuid=school_year.uuid)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:school_year_detail", uuid=school_year.uuid)

    def test_only_school_year_for_user(self):
        """A user may only view their own school years."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:school_year_detail", uuid=school_year.uuid)

        self.response_404(response)
