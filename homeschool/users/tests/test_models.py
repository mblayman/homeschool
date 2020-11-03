from homeschool.accounts.models import Account
from homeschool.schools.models import School
from homeschool.schools.tests.factories import SchoolFactory
from homeschool.test import TestCase


class TestUser(TestCase):
    def test_school(self):
        user = self.make_user()
        SchoolFactory(admin=user)
        school = SchoolFactory(admin=user)

        assert user.school == school

    def test_create_school(self):
        """A new user automatically has a school created."""
        user = self.make_user()

        assert user.school == School.objects.get(admin=user)

    def test_create_account(self):
        """A new user automatically has an account created."""
        user = self.make_user()

        assert Account.objects.filter(user=user).exists()
