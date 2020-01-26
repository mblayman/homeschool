import uuid

from homeschool.courses.models import Course
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

    def test_has_days_of_week(self):
        days_of_week = Course.MONDAY + Course.TUESDAY
        course = CourseFactory(days_of_week=days_of_week)

        self.assertEqual(course.days_of_week, days_of_week)

    def test_total_week_days(self):
        days_of_week = Course.MONDAY + Course.TUESDAY + Course.THURSDAY + Course.SUNDAY
        course = CourseFactory(days_of_week=days_of_week)

        self.assertEqual(course.total_week_days, 4)

        days_of_week = (
            Course.MONDAY
            + Course.TUESDAY
            + Course.WEDNESDAY
            + Course.THURSDAY
            + Course.FRIDAY
            + Course.SATURDAY
            + Course.SUNDAY
        )
        course = CourseFactory(days_of_week=days_of_week)

        self.assertEqual(course.total_week_days, 7)


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

    def test_has_duration(self):
        duration = 30
        task = CourseTaskFactory(duration=duration)

        self.assertEqual(task.duration, duration)
