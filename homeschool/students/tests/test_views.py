import datetime

from django.utils import timezone
from freezegun import freeze_time

from homeschool.courses.models import Course
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.schools.tests.factories import SchoolYearFactory
from homeschool.students.models import Grade
from homeschool.students.tests.factories import (
    CourseworkFactory,
    GradeFactory,
    StudentFactory,
)
from homeschool.test import TestCase


class TestStudentsIndexView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("students:index")

    def test_get(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("students:index")


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
        CourseworkFactory(course_task=task_1, student=student)
        task_2 = CourseTaskFactory(course=course)
        GradedWorkFactory(course_task=task_2)
        today = timezone.now().date() + datetime.timedelta(days=2)

        with self.login(user):
            self.get_check_200(
                "students:course", uuid=student.uuid, course_uuid=course.uuid
            )

        self.assertContext(
            "task_items",
            [{"course_task": task_2, "planned_date": today, "has_graded_work": True}],
        )

    @freeze_time("2020-02-10")  # Monday
    def test_has_tasks_with_completed(self):
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
                "students:course",
                uuid=student.uuid,
                course_uuid=course.uuid,
                data={"completed_tasks": "1"},
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

        with self.login(user):
            self.get("students:grade")

        self.assertContext(
            "work_to_grade",
            [
                {"student": student_1, "graded_work": []},
                {"student": student_2, "graded_work": []},
            ],
        )

    def test_not_other_students(self):
        user = self.make_user()
        StudentFactory()

        with self.login(user):
            self.get("students:grade")

        self.assertContext("work_to_grade", [])

    def test_fetch_graded_work(self):
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(school=user.school)
        graded_work_1 = GradedWorkFactory(
            course_task__course__grade_level__school_year=school_year
        )
        CourseworkFactory(student=student, course_task=graded_work_1.course_task)
        GradeFactory(student=student, graded_work=graded_work_1)
        graded_work_2 = GradedWorkFactory(
            course_task__course__grade_level__school_year=school_year
        )
        CourseworkFactory(student=student, course_task=graded_work_2.course_task)

        with self.login(user):
            self.get("students:grade")

        self.assertContext(
            "work_to_grade", [{"student": student, "graded_work": [graded_work_2]}]
        )

    def test_not_graded_work_from_other_school(self):
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(school=user.school)
        graded_work_1 = GradedWorkFactory(
            course_task__course__grade_level__school_year=school_year
        )
        CourseworkFactory(student=student, course_task=graded_work_1.course_task)
        graded_work_2 = GradedWorkFactory()
        CourseworkFactory(course_task=graded_work_2.course_task)

        with self.login(user):
            self.get("students:grade")

        self.assertContext(
            "work_to_grade", [{"student": student, "graded_work": [graded_work_1]}]
        )

    def test_grade(self):
        user = self.make_user()
        student = StudentFactory(school=user.school)
        school_year = SchoolYearFactory(school=user.school)
        graded_work = GradedWorkFactory(
            course_task__course__grade_level__school_year=school_year
        )
        graded_work_2 = GradedWorkFactory(
            course_task__course__grade_level__school_year=school_year
        )
        data = {
            f"graded_work-{student.id}-{graded_work.id}": "100",
            f"graded_work-{student.id}-{graded_work_2.id}": "",
        }

        with self.login(user):
            response = self.post("students:grade", data=data)

        self.response_302(response)
        self.assertEqual(response.get("Location"), self.reverse("core:daily"))
        grade = Grade.objects.get(student=student, graded_work=graded_work)
        self.assertEqual(grade.score, 100)
