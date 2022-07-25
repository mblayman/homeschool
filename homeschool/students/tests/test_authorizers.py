from homeschool.students.authorizers import enrollment_authorized
from homeschool.students.tests.factories import EnrollmentFactory
from homeschool.test import TestCase


class TestEnrollmentAuthorized(TestCase):
    def test_permitted_course(self):
        """An enrollment is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        enrollment = EnrollmentFactory(
            grade_level__school_year__school__admin=request.user
        )

        assert enrollment_authorized(request, pk=enrollment.pk)

    def test_denied_course(self):
        """Another enrollment is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        enrollment = EnrollmentFactory()

        assert not enrollment_authorized(request, pk=enrollment.pk)
