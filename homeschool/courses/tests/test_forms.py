from homeschool.courses.forms import CourseForm, CourseResourceForm, CourseTaskForm
from homeschool.courses.tests.factories import CourseFactory
from homeschool.schools.models import SchoolYear
from homeschool.schools.tests.factories import GradeLevelFactory, SchoolYearFactory
from homeschool.test import TestCase


class TestCourseForm(TestCase):
    def test_course_days_on_school_year_days(self):
        """A course must run on days that are in the school year's set days."""
        user = self.make_user()
        school_year = SchoolYearFactory(
            school=user.school, days_of_week=SchoolYear.MONDAY
        )
        grade_level = GradeLevelFactory(school_year=school_year)
        data = {
            "name": "Will Not Work",
            "default_task_duration": "30",
            "grade_levels": [str(grade_level.id)],
            "tuesday": "on",
        }
        form = CourseForm(school_year, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert (
            "The course must run within school year days: Monday"
            in form.non_field_errors()
        )


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
