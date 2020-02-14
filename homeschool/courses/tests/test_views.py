from homeschool.courses.models import CourseTask
from homeschool.courses.tests.factories import CourseFactory, CourseTaskFactory
from homeschool.test import TestCase


class TestCourseDetailView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:detail", uuid=course.uuid)

    def test_get(self):
        user = self.make_user()
        course = CourseFactory(grade_level__school_year__school__admin=user)

        with self.login(user):
            self.get_check_200("courses:detail", uuid=course.uuid)


class TestCourseTaskCreateView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:task_create", uuid=course.uuid)

    def test_get(self):
        user = self.make_user()
        course = CourseFactory(grade_level__school_year__school__admin=user)

        with self.login(user):
            self.get_check_200("courses:task_create", uuid=course.uuid)

    def test_post(self):
        user = self.make_user()
        course = CourseFactory(grade_level__school_year__school__admin=user)
        data = {"course": str(course.id), "description": "A new task", "duration": "30"}

        with self.login(user):
            response = self.post("courses:task_create", uuid=course.uuid, data=data)

        self.assertEqual(CourseTask.objects.count(), 1)
        task = CourseTask.objects.get(course=course)
        self.assertEqual(task.description, data["description"])
        self.assertEqual(task.duration, int(data["duration"]))
        self.response_302(response)
        self.assertEqual(
            response.get("Location"), self.reverse("courses:detail", uuid=course.uuid)
        )
        self.assertIsNone(task.graded_work)

    def test_has_create(self):
        user = self.make_user()
        course = CourseFactory(grade_level__school_year__school__admin=user)

        with self.login(user):
            self.get("courses:task_create", uuid=course.uuid)

        self.assertContext("create", True)

    def test_has_course(self):
        user = self.make_user()
        course = CourseFactory(grade_level__school_year__school__admin=user)

        with self.login(user):
            self.get("courses:task_create", uuid=course.uuid)

        self.assertContext("course", course)

    def test_after_task(self):
        user = self.make_user()
        course = CourseFactory(grade_level__school_year__school__admin=user)
        data = {"course": str(course.id), "description": "A new task", "duration": "30"}
        task_1 = CourseTaskFactory(course=course)
        task_2 = CourseTaskFactory(course=course)
        url = self.reverse("courses:task_create", uuid=course.uuid)
        url += f"?previous_task={task_1.uuid}"

        with self.login(user):
            self.post(url, data=data)

        task_3 = CourseTask.objects.get(description="A new task")
        self.assertEqual(list(CourseTask.objects.all()), [task_1, task_3, task_2])

    def test_is_graded(self):
        user = self.make_user()
        course = CourseFactory(grade_level__school_year__school__admin=user)
        data = {
            "course": str(course.id),
            "description": "A new task",
            "duration": "30",
            "is_graded": "on",
        }

        with self.login(user):
            self.post("courses:task_create", uuid=course.uuid, data=data)

        self.assertEqual(CourseTask.objects.count(), 1)
        task = CourseTask.objects.get(course=course)
        self.assertIsNotNone(task.graded_work)


class TestCourseTaskUpdateView(TestCase):
    def test_unauthenticated_access(self):
        task = CourseTaskFactory()
        self.assertLoginRequired("courses:task_edit", uuid=task.uuid)

    def test_get(self):
        user = self.make_user()
        task = CourseTaskFactory(course__grade_level__school_year__school__admin=user)

        with self.login(user):
            self.get_check_200("courses:task_edit", uuid=task.uuid)

    def test_get_other_user(self):
        user = self.make_user()
        task = CourseTaskFactory()

        with self.login(user):
            response = self.get("courses:task_edit", uuid=task.uuid)

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
            response = self.post("courses:task_edit", uuid=task.uuid, data=data)

        task.refresh_from_db()
        self.assertEqual(task.description, data["description"])
        self.assertEqual(task.duration, data["duration"])
        self.response_302(response)

    def test_redirect_next(self):
        next_url = "/another/location/"
        user = self.make_user()
        task = CourseTaskFactory(course__grade_level__school_year__school__admin=user)
        data = {"description": "new description", "duration": 15}
        url = self.reverse("courses:task_edit", uuid=task.uuid)
        url += f"?next={next_url}"

        with self.login(user):
            response = self.post(url, data=data)

        self.response_302(response)
        self.assertIn(next_url, response.get("Location"))


class TestCourseTaskDeleteView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        task = CourseTaskFactory(course=course)
        self.assertLoginRequired(
            "courses:task_delete", uuid=course.uuid, task_uuid=task.uuid
        )

    def test_post(self):
        user = self.make_user()
        course = CourseFactory(grade_level__school_year__school__admin=user)
        task = CourseTaskFactory(course=course)

        with self.login(user):
            response = self.post(
                "courses:task_delete", uuid=course.uuid, task_uuid=task.uuid
            )

        self.assertEqual(CourseTask.objects.count(), 0)
        self.response_302(response)
        self.assertEqual(
            response.get("Location"), self.reverse("courses:detail", uuid=course.uuid)
        )

    def test_post_other_user(self):
        user = self.make_user()
        course = CourseFactory()
        task = CourseTaskFactory(course=course)

        with self.login(user):
            response = self.get(
                "courses:task_delete", uuid=course.uuid, task_uuid=task.uuid
            )

        self.response_404(response)
