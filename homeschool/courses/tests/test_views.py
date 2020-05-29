from homeschool.courses.models import Course, CourseTask, GradedWork
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.schools.tests.factories import GradeLevelFactory
from homeschool.test import TestCase


class TestCourseDetailView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:detail", uuid=course.uuid)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("courses:detail", uuid=course.uuid)

    def test_grade_level_name_with_task(self):
        """Any grade level specific task has the grade level's name next to it."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory(course=course, grade_level=grade_level)

        with self.login(user):
            self.get("courses:detail", uuid=course.uuid)

        self.assertResponseContains(grade_level.name)


class TestCourseEditView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:edit", uuid=course.uuid)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("courses:edit", uuid=course.uuid)

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {"name": "New course name", "wednesday": "on", "friday": "on"}

        with self.login(user):
            self.post("courses:edit", uuid=course.uuid, data=data)

        course.refresh_from_db()
        assert course.name == "New course name"
        assert course.days_of_week == Course.WEDNESDAY + Course.FRIDAY


class TestCourseTaskCreateView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:task_create", uuid=course.uuid)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("courses:task_create", uuid=course.uuid)

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {"course": str(course.id), "description": "A new task", "duration": "30"}

        with self.login(user):
            response = self.post("courses:task_create", uuid=course.uuid, data=data)

        assert CourseTask.objects.count() == 1
        task = CourseTask.objects.get(course=course)
        assert task.description == data["description"]
        assert task.duration == int(data["duration"])
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "courses:detail", uuid=course.uuid
        )
        assert not hasattr(task, "graded_work")

    def test_has_create(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get("courses:task_create", uuid=course.uuid)

        self.assertContext("create", True)

    def test_redirect_next(self):
        next_url = "/another/location/"
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "course": str(course.id),
            "description": "new description",
            "duration": 15,
        }
        url = self.reverse("courses:task_create", uuid=course.uuid)
        url += f"?next={next_url}"

        with self.login(user):
            response = self.post(url, data=data)

        self.response_302(response)
        assert next_url in response.get("Location")

    def test_has_course(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get("courses:task_create", uuid=course.uuid)

        self.assertContext("course", course)

    def test_after_task(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {"course": str(course.id), "description": "A new task", "duration": "30"}
        task_1 = CourseTaskFactory(course=course)
        task_2 = CourseTaskFactory(course=course)
        url = self.reverse("courses:task_create", uuid=course.uuid)
        url += f"?previous_task={task_1.uuid}"

        with self.login(user):
            self.post(url, data=data)

        task_3 = CourseTask.objects.get(description="A new task")
        assert list(CourseTask.objects.all()) == [task_1, task_3, task_2]

    def test_is_graded(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "course": str(course.id),
            "description": "A new task",
            "duration": "30",
            "is_graded": "on",
        }

        with self.login(user):
            self.post("courses:task_create", uuid=course.uuid, data=data)

        assert CourseTask.objects.count() == 1
        task = CourseTask.objects.get(course=course)
        assert task.graded_work is not None


class TestCourseTaskUpdateView(TestCase):
    def test_unauthenticated_access(self):
        task = CourseTaskFactory()
        self.assertLoginRequired("courses:task_edit", uuid=task.uuid)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)

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
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(
            description="some description", duration=30, course=course
        )
        data = {
            "course": str(task.course.id),
            "description": "new description",
            "duration": 15,
        }

        with self.login(user):
            response = self.post("courses:task_edit", uuid=task.uuid, data=data)

        task.refresh_from_db()
        assert task.description == data["description"]
        assert task.duration == data["duration"]
        self.response_302(response)

    def test_has_course(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)

        with self.login(user):
            self.get("courses:task_edit", uuid=task.uuid)

        self.assertContext("course", task.course)

    def test_redirect_next(self):
        next_url = "/another/location/"
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)
        data = {
            "course": str(task.course.id),
            "description": "new description",
            "duration": 15,
        }
        url = self.reverse("courses:task_edit", uuid=task.uuid)
        url += f"?next={next_url}"

        with self.login(user):
            response = self.post(url, data=data)

        self.response_302(response)
        assert next_url in response.get("Location")

    def test_is_graded(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(
            description="some description", duration=30, course=course
        )
        data = {
            "course": str(task.course.id),
            "description": "new description",
            "duration": 15,
            "is_graded": "on",
        }

        with self.login(user):
            self.post("courses:task_edit", uuid=task.uuid, data=data)

        task.refresh_from_db()
        assert task.graded_work is not None

    def test_keep_graded(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(
            description="some description", duration=30, course=course
        )
        GradedWorkFactory(course_task=task)
        data = {
            "course": str(task.course.id),
            "description": "new description",
            "duration": 15,
            "is_graded": "on",
        }

        with self.login(user):
            self.post("courses:task_edit", uuid=task.uuid, data=data)

        task.refresh_from_db()
        assert task.graded_work is not None
        assert GradedWork.objects.count() == 1

    def test_remove_graded(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(
            description="some description", duration=30, course=course
        )
        GradedWorkFactory(course_task=task)
        data = {
            "course": str(task.course.id),
            "description": "new description",
            "duration": 15,
        }

        with self.login(user):
            self.post("courses:task_edit", uuid=task.uuid, data=data)

        task.refresh_from_db()
        assert not hasattr(task, "graded_work")


class TestCourseTaskDeleteView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        task = CourseTaskFactory(course=course)
        self.assertLoginRequired(
            "courses:task_delete", uuid=course.uuid, task_uuid=task.uuid
        )

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)

        with self.login(user):
            response = self.post(
                "courses:task_delete", uuid=course.uuid, task_uuid=task.uuid
            )

        assert CourseTask.objects.count() == 0
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "courses:detail", uuid=course.uuid
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
