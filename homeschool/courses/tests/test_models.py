import pytest

from homeschool.courses.exceptions import NoSchoolYearError
from homeschool.courses.models import Course, CourseTask
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseResourceFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.schools.tests.factories import GradeLevelFactory
from homeschool.test import TestCase


class TestCourse(TestCase):
    def test_factory(self):
        course = CourseFactory()

        assert course is not None
        assert course.name != ""
        assert course.default_task_duration == 30

    def test_str(self):
        course = CourseFactory()

        assert str(course) == course.name

    def test_has_name(self):
        name = "Calculus I"
        course = CourseFactory(name=name)

        assert course.name == name

    def test_has_default_task_duration(self):
        default_task_duration = 45
        course = CourseFactory(default_task_duration=default_task_duration)

        assert course.default_task_duration == default_task_duration

    def test_has_grade_level(self):
        grade_level = GradeLevelFactory()
        course = CourseFactory(grade_levels=[grade_level])

        assert list(course.grade_levels.all()) == [grade_level]

    def test_has_days_of_week(self):
        days_of_week = Course.MONDAY + Course.TUESDAY
        course = CourseFactory(days_of_week=days_of_week)

        assert course.days_of_week == days_of_week

    def test_is_running(self):
        running_course = CourseFactory()
        not_running_course = CourseFactory(days_of_week=Course.NO_DAYS)

        assert running_course.is_running
        assert not not_running_course.is_running

    def test_has_many_grade_levels(self):
        course = CourseFactory()
        course_multiple_grade_levels = CourseFactory(
            grade_levels=[GradeLevelFactory(), GradeLevelFactory()]
        )

        assert not course.has_many_grade_levels
        assert course_multiple_grade_levels.has_many_grade_levels

    def test_no_school_year(self):
        """A course without a school year raises an error."""
        course = CourseFactory()

        with pytest.raises(NoSchoolYearError):
            _ = course.school_year


class TestCourseTask(TestCase):
    def test_factory(self):
        task = CourseTaskFactory.create()
        other_task = CourseTaskFactory.build()

        assert task is not None
        assert task.description != ""
        assert not hasattr(task, "graded_work")
        assert other_task.id is None
        assert task.grade_level is None
        assert task.resource is None

    def test_str(self):
        task = CourseTaskFactory()

        assert str(task) == task.description

    def test_str_with_resource(self):
        """A resource title is included in the str representation."""
        resource = CourseResourceFactory()
        task = CourseTaskFactory(resource=resource)

        assert str(task) == f"{resource.title}: {task.description}"

    def test_has_course(self):
        course = CourseFactory()
        task = CourseTaskFactory(course=course)

        assert task.course == course

    def test_has_description(self):
        description = "Chapter 1 from SICP"
        task = CourseTaskFactory(description=description)

        assert task.description == description

    def test_has_duration(self):
        duration = 30
        task = CourseTaskFactory(duration=duration)

        assert task.duration == duration

    def test_has_graded_work(self):
        graded_work = GradedWorkFactory()
        task = CourseTaskFactory()
        task.graded_work = graded_work
        task.save()

        assert task.graded_work == graded_work

    def test_has_grade_level(self):
        grade_level = GradeLevelFactory()
        task = CourseTaskFactory.create(grade_level=grade_level)

        assert task.grade_level == grade_level

    def test_order_with_respect_to_course(self):
        """Moving a task will only affect tasks within a individual course."""
        grade_level = GradeLevelFactory()
        course_1 = CourseFactory(grade_levels=[grade_level])
        course_2 = CourseFactory(grade_levels=[grade_level])
        task_1 = CourseTaskFactory(course=course_1)
        task_2 = CourseTaskFactory(course=course_2)
        task_3 = CourseTaskFactory(course=course_1)

        task_3.below(task_1)

        assert list(CourseTask.objects.all()) == [task_1, task_2, task_3]

    def test_get_by_id(self):
        """A user can get a task by its ID for their courses."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        expected_task = CourseTaskFactory(course__grade_levels=[grade_level])

        task = CourseTask.get_by_id(user, str(expected_task.id))

        assert task == expected_task

    def test_get_by_id_invalid_user(self):
        """Another user cannot get a task that is inaccessible."""
        user = self.make_user()
        grade_level = GradeLevelFactory()
        other_task = CourseTaskFactory(course__grade_levels=[grade_level])

        task = CourseTask.get_by_id(user, str(other_task.id))

        assert task is None

    def test_get_by_id_bad_id(self):
        """A bad ID returns no task."""
        user = self.make_user()

        task = CourseTask.get_by_id(user, "boom")

        assert task is None

    def test_is_graded(self):
        """Check if a task has associated graded work."""
        graded_work = GradedWorkFactory()
        graded_task = CourseTaskFactory()
        graded_task.graded_work = graded_work
        graded_task.save()
        task = CourseTaskFactory()

        assert graded_task.is_graded
        assert not task.is_graded


class TestGradedWork(TestCase):
    def test_factory(self):
        graded_work = GradedWorkFactory()

        assert graded_work is not None


class TestCourseResource(TestCase):
    def test_factory(self):
        resource = CourseResourceFactory()

        assert resource.title != ""
        assert resource.details != ""
        assert resource.course is not None

    def test_str(self):
        resource = CourseResourceFactory()

        assert str(resource) == resource.title
