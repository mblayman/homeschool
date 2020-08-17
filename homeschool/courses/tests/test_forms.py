from homeschool.courses.forms import CourseResourceForm, CourseTaskForm
from homeschool.courses.tests.factories import CourseFactory
from homeschool.test import TestCase


class TestCourseResourceForm(TestCase):
    def test_invalid_course(self):
        """An invalid course is a validation error."""
        user = self.make_user()
        data = {
            "course": "nope",
            "title": "This will not work.",
            "details": "The course ID is invalid.",
        }
        form = CourseResourceForm(user=user, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "Invalid course." in form.non_field_errors()

    def test_only_users_courses(self):
        """A user may not assign a resource to another user's course."""
        user = self.make_user()
        course = CourseFactory()
        data = {
            "course": str(course.id),
            "title": "Charlotte's Web",
            "details": "That's some pig.",
        }
        form = CourseResourceForm(user=user, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "You may not add a resource to another" in form.non_field_errors()[0]


class TestCourseTaskForm(TestCase):
    def test_invalid_course(self):
        """An invalid course is a validation error."""
        user = self.make_user()
        data = {"course": "nope", "description": "A new task", "duration": "30"}
        form = CourseTaskForm(user=user, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "Invalid course." in form.non_field_errors()

    def test_only_users_courses(self):
        """A user may not assign a task to another user's course."""
        user = self.make_user()
        course = CourseFactory()
        data = {"course": str(course.id), "description": "A new task", "duration": "30"}
        form = CourseTaskForm(user=user, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "You may not add a task to another" in form.non_field_errors()[0]
