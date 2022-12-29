from homeschool.courses.authorizers import (
    course_authorized,
    resource_authorized,
    task_authorized,
)
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseResourceFactory,
    CourseTaskFactory,
)
from homeschool.schools.tests.factories import GradeLevelFactory
from homeschool.test import TestCase


class TestCourseAuthorized(TestCase):
    def test_permitted_course(self):
        """A course is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=request.user.school)  # type: ignore  # Issue 762 # noqa
        course = CourseFactory(grade_levels=[grade_level])

        assert course_authorized(request, pk=course.pk)

    def test_denied_course(self):
        """Another course is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        course = CourseFactory()

        assert not course_authorized(request, pk=course.pk)


class TestCourseTaskAuthorized(TestCase):
    def test_permitted_course_task(self):
        """A course task is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=request.user.school)  # type: ignore  # Issue 762 # noqa
        course = CourseFactory(grade_levels=[grade_level])
        course_task = CourseTaskFactory(course=course)

        assert task_authorized(request, pk=course_task.pk)

    def test_denied_course_task(self):
        """Another course task is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        course_task = CourseTaskFactory()

        assert not task_authorized(request, pk=course_task.pk)


class TestCourseResourceAuthorized(TestCase):
    def test_permitted_resource(self):
        """A course resource is accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=request.user.school)  # type: ignore  # Issue 762 # noqa
        course = CourseFactory(grade_levels=[grade_level])
        resource = CourseResourceFactory(course=course)

        assert resource_authorized(request, pk=resource.pk)

    def test_denied_resource(self):
        """Another course resource is not accessible to a user."""
        request = self.rf.get("/")
        request.user = self.make_user()
        resource = CourseResourceFactory()

        assert not resource_authorized(request, pk=resource.pk)
