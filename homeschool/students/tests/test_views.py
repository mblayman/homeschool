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


class TestGradeView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("students:grade")

    def test_get(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("students:grade")

    def test_fetch_students(self):
        user = self.make_user()
        student_1 = StudentFactory(school=user.school)
        student_2 = StudentFactory(school=user.school)
        query_params = {
            "students": ",".join([str(student_1.uuid), str(student_2.uuid)])
        }

        with self.login(user):
            self.get("students:grade", data=query_params)

        self.assertContext(
            "students",
            [
                {"student": student_1, "graded_work": []},
                {"student": student_2, "graded_work": []},
            ],
        )

    def test_not_other_students(self):
        user = self.make_user()
        student = StudentFactory()
        query_params = {"students": ",".join([str(student.uuid)])}

        with self.login(user):
            self.get("students:grade", data=query_params)

        self.assertContext("students", [])

    def test_fetch_graded_work(self):
        user = self.make_user()
        student = StudentFactory(school=user.school)
        graded_work_1 = GradedWorkFactory(
            course_task__course__grade_level__school_year__school=user.school
        )
        graded_work_2 = GradedWorkFactory(
            course_task__course__grade_level__school_year__school=user.school
        )
        query_params = {
            "students": str(student.uuid),
            f"{student.uuid}_graded_work": ",".join(
                [str(graded_work_1.id), str(graded_work_2.id)]
            ),
        }

        with self.login(user):
            self.get("students:grade", data=query_params)

        self.assertContext(
            "students",
            [{"student": student, "graded_work": [graded_work_1, graded_work_2]}],
        )

    def test_not_graded_work_from_other_school(self):
        user = self.make_user()
        student = StudentFactory(school=user.school)
        graded_work_1 = GradedWorkFactory(
            course_task__course__grade_level__school_year__school=user.school
        )
        graded_work_2 = GradedWorkFactory()
        query_params = {
            "students": str(student.uuid),
            f"{student.uuid}_graded_work": ",".join(
                [str(graded_work_1.id), str(graded_work_2.id)]
            ),
        }

        with self.login(user):
            self.get("students:grade", data=query_params)

        self.assertContext(
            "students", [{"student": student, "graded_work": [graded_work_1]}]
        )
