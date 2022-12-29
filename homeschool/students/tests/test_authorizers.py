from django.contrib.auth.models import AnonymousUser

from homeschool.students.authorizers import enrollment_authorized, student_authorized
from homeschool.students.tests.factories import EnrollmentFactory, StudentFactory
from homeschool.test import TestCase


class TestEnrollmentAuthorized(TestCase):
    def test_permitted_enrollment(self):
        """An enrollment is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        enrollment = EnrollmentFactory.create(
            grade_level__school_year__school__admin=request.user
        )

        assert enrollment_authorized(request, pk=enrollment.pk)

    def test_denied_enrollment(self):
        """Another enrollment is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        enrollment = EnrollmentFactory.create()

        assert not enrollment_authorized(request, pk=enrollment.pk)


class TestStudentAuthorized(TestCase):
    def test_permitted_student(self):
        """A student is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        student = StudentFactory.create(school__admin=request.user)

        assert student_authorized(request, pk=student.pk)

    def test_denied_student(self):
        """Another student is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        student = StudentFactory.create()

        assert not student_authorized(request, pk=student.pk)

    def test_anonymous_user(self):
        """A student is not accessible to an anonymous user."""
        request = self.rf.get("/")
        request.user = AnonymousUser()
        student = StudentFactory.create()

        assert not student_authorized(request, pk=student.pk)
