import uuid

from homeschool.courses.tests.factories import CourseFactory, CourseTaskFactory
from homeschool.schools.tests.factories import GradeLevelFactory
from homeschool.test import TestCase


class TestCourse(TestCase):
    def test_factory(self):
        course = CourseFactory()

        self.assertIsNotNone(course)
        self.assertNotEqual(course.name, "")

    def test_has_name(self):
        name = "Calculus I"
        course = CourseFactory(name=name)

        self.assertEqual(course.name, name)

    def test_has_grade_level(self):
        grade_level = GradeLevelFactory()
        course = CourseFactory(grade_level=grade_level)

        self.assertEqual(course.grade_level, grade_level)


class TestCourseTask(TestCase):
    def test_factory(self):
        task = CourseTaskFactory()

        self.assertIsNotNone(task)
        self.assertNotEqual(str(task.uuid), "")
        self.assertNotEqual(task.description, "")

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
