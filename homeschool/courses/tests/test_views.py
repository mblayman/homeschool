from homeschool.courses.tests.factories import CourseTaskFactory
from homeschool.test import TestCase


class TestCourseTaskUpdateView(TestCase):
    def test_unauthenticated_access(self):
        task = CourseTaskFactory()
        self.assertLoginRequired("courses:course_task_edit", uuid=task.uuid)

    def test_get(self):
        user = self.make_user()
        task = CourseTaskFactory(course__grade_level__school_year__school__admin=user)

        with self.login(user):
            self.get_check_200("courses:course_task_edit", uuid=task.uuid)

    def test_get_other_user(self):
        user = self.make_user()
        task = CourseTaskFactory()

        with self.login(user):
            response = self.get("courses:course_task_edit", uuid=task.uuid)

        self.response_404(response)

    def test_post(self):
        user = self.make_user()
        task = CourseTaskFactory(
            description="some description",
            duration=30,
            course__grade_level__school_year__school__admin=user,
        )
        data = {"description": "new description", "duration": 15}

        with self.login(user):
            response = self.post("courses:course_task_edit", uuid=task.uuid, data=data)

        task.refresh_from_db()
        self.assertEqual(task.description, data["description"])
        self.assertEqual(task.duration, data["duration"])
        self.response_302(response)
