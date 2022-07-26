from homeschool.students.authorizers import enrollment_authorized, student_authorized
from homeschool.students.tests.factories import EnrollmentFactory, StudentFactory
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


class TestStudentAuthorized(TestCase):
    def test_permitted_course(self):
        """A student is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        student = StudentFactory(school__admin=request.user)

        assert student_authorized(request, pk=student.pk)

    def test_denied_course(self):
        """Another student is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        student = StudentFactory()

        assert not student_authorized(request, pk=student.pk)
