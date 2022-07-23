from django.test import RequestFactory

from homeschool.denied.authorizers import any_authorized, staff_authorized
from homeschool.test import TestCase
from homeschool.users.tests.factories import UserFactory


class TestAnyAuthorized(TestCase):
    rf = RequestFactory()

    def test_authorized(self):
        """Any authorized use is permitted."""
        request = self.rf.get("/")

        assert any_authorized(request)


class TestStaffAuthorized(TestCase):
    rf = RequestFactory()

    def test_non_staff(self):
        """Non-staff access is not permitted."""
        request = self.rf.get("/")
        request.user = UserFactory(is_staff=False)

        assert not staff_authorized(request)

    def test_staff(self):
        """Staff access is permitted."""
        request = self.rf.get("/")
        request.user = UserFactory(is_staff=True)

        assert staff_authorized(request)
