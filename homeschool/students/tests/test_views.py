import datetime

from django.utils import timezone
from freezegun import freeze_time

from homeschool.courses.models import Course
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.students.tests.factories import CourseworkFactory, StudentFactory
from homeschool.test import TestCase


class TestStudentCourseView(TestCase):
    def test_unauthenticated_access(self):
        student = StudentFactory()
        course = CourseFactory()
        self.assertLoginRequired(
            "students:course", uuid=student.uuid, course_uuid=course.uuid
        )

    def test_get(self):
        user = self.make_user()
        student = StudentFactory(school=user.school)
        course = CourseFactory(grade_level__school_year__school=user.school)

        with self.login(user):
            self.get_check_200(
                "students:course", uuid=student.uuid, course_uuid=course.uuid
            )

    def test_other_user(self):
        user = self.make_user()
        student = StudentFactory()
        course = CourseFactory()

        with self.login(user):
            response = self.get(
                "students:course", uuid=student.uuid, course_uuid=course.uuid
            )

        self.response_404(response)

    def test_has_student(self):
        user = self.make_user()
        student = StudentFactory(school=user.school)
        course = CourseFactory(grade_level__school_year__school=user.school)

        with self.login(user):
            self.get_check_200(
                "students:course", uuid=student.uuid, course_uuid=course.uuid
            )

        self.assertContext("student", student)

    def test_has_course(self):
        user = self.make_user()
        student = StudentFactory(school=user.school)
        course = CourseFactory(grade_level__school_year__school=user.school)

        with self.login(user):
            self.get_check_200(
                "students:course", uuid=student.uuid, course_uuid=course.uuid
            )

        self.assertContext("course", course)

    @freeze_time("2020-02-10")  # Monday
    def test_has_tasks(self):
        user = self.make_user()
        student = StudentFactory(school=user.school)
        course = CourseFactory(
            grade_level__school_year__school=user.school,
            days_of_week=Course.WEDNESDAY + Course.THURSDAY,
        )
        task_1 = CourseTaskFactory(course=course)
        coursework = CourseworkFactory(course_task=task_1, student=student)
        task_2 = CourseTaskFactory(course=course)
        GradedWorkFactory(course_task=task_2)
        today = timezone.now().date() + datetime.timedelta(days=2)

        with self.login(user):
            self.get_check_200(
                "students:course", uuid=student.uuid, course_uuid=course.uuid
            )

        self.assertContext(
            "task_items",
            [
                {
                    "course_task": task_1,
                    "coursework": coursework,
                    "has_graded_work": False,
                },
                {"course_task": task_2, "planned_date": today, "has_graded_work": True},
            ],
        )
