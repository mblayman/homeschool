from django.test import TestCase

from homeschool.schools.tests.factories import SchoolFactory
from homeschool.users.tests.factories import UserFactory


class TestSchool(TestCase):
    def test_factory(self):
        """A school is created."""
        school = SchoolFactory()

        self.assertIsNotNone(school)

    def test_school_has_admin(self):
        """A school has an administrator."""
        user = UserFactory()
        school = SchoolFactory(admin=user)

        self.assertEqual(school.admin, user)
