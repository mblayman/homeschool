import uuid

from homeschool.courses.models import Course, CourseTask
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.schools.tests.factories import GradeLevelFactory
from homeschool.test import TestCase


class TestCourse(TestCase):
    def test_factory(self):
        course = CourseFactory()

        self.assertIsNotNone(course)
        self.assertNotEqual(course.name, "")

    def test_has_uuid(self):
        course_uuid = uuid.uuid4()
        course = CourseFactory(uuid=course_uuid)

        self.assertEqual(course.uuid, course_uuid)

    def test_has_name(self):
        name = "Calculus I"
        course = CourseFactory(name=name)

        self.assertEqual(course.name, name)

    def test_has_grade_level(self):
        grade_level = GradeLevelFactory()
        course = CourseFactory(grade_level=grade_level)

        self.assertEqual(course.grade_level, grade_level)

    def test_has_days_of_week(self):
        days_of_week = Course.MONDAY + Course.TUESDAY
        course = CourseFactory(days_of_week=days_of_week)

        self.assertEqual(course.days_of_week, days_of_week)


class TestGradedWork(TestCase):
    def test_factory(self):
        graded_work = GradedWorkFactory()

        self.assertIsNotNone(graded_work)


class TestCourseTask(TestCase):
    def test_factory(self):
        task = CourseTaskFactory()

        self.assertIsNotNone(task)
        self.assertNotEqual(str(task.uuid), "")
        self.assertNotEqual(task.description, "")
        self.assertIsNone(task.graded_work)

    def test_has_course(self):
        course = CourseFactory()
        task = CourseTaskFactory(course=course)

        self.assertEqual(task.course, course)

    def test_has_uuid(self):
        task_uuid = uuid.uuid4()
        task = CourseTaskFactory(uuid=task_uuid)

        self.assertEqual(task.uuid, task_uuid)

    def test_has_description(self):
        description = "Chapter 1 from SICP"
        task = CourseTaskFactory(description=description)

        self.assertEqual(task.description, description)

    def test_has_duration(self):
        duration = 30
        task = CourseTaskFactory(duration=duration)

        self.assertEqual(task.duration, duration)

    def test_has_graded_work(self):
        graded_work = GradedWorkFactory()
        task = CourseTaskFactory(graded_work=graded_work)

        self.assertEqual(task.graded_work, graded_work)

    def test_order_with_respect_to_course(self):
        """Moving a task will only affect tasks within a individual course."""
        course_1 = CourseFactory()
        course_2 = CourseFactory(grade_level=course_1.grade_level)
        task_1 = CourseTaskFactory(course=course_1)
        task_2 = CourseTaskFactory(course=course_2)
        task_3 = CourseTaskFactory(course=course_1)

        task_3.below(task_1)

        self.assertEqual(list(CourseTask.objects.all()), [task_1, task_2, task_3])
