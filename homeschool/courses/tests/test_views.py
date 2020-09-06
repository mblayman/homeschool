import datetime

from homeschool.courses.models import Course, CourseResource, CourseTask, GradedWork
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseResourceFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.schools.tests.factories import GradeLevelFactory, SchoolYearFactory
from homeschool.test import TestCase


class TestCourseCreateView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("courses:create")

    def test_get(self):
        user = self.make_user()
        SchoolYearFactory(school__admin=user)

        with self.login(user):
            self.get_check_200("courses:create")

        assert self.get_context("create")

    def test_school_year_uuid(self):
        """A school year is fetched from the querystring."""
        user = self.make_user()
        today = user.get_local_today()
        # Use dates in the past so the school year won't be a "current" school year.
        school_year = SchoolYearFactory(
            school__admin=user,
            start_date=today - datetime.timedelta(days=365),
            end_date=today - datetime.timedelta(days=1),
        )

        with self.login(user):
            self.get_check_200(
                "courses:create", data={"school_year": str(school_year.uuid)}
            )

        form = self.get_context("form")
        assert form.school_year == school_year

    def test_school_year_only_user_school_years(self):
        """A school year from the querystring can only be a user's school years."""
        user = self.make_user()
        user_school_year = SchoolYearFactory(school__admin=user)
        school_year = SchoolYearFactory()

        with self.login(user):
            self.get_check_200(
                "courses:create", data={"school_year": str(school_year.uuid)}
            )

        form = self.get_context("form")
        assert form.school_year == user_school_year

    def test_school_year_from_user(self):
        """A school year is fetched from the user if not provided on the querystring."""
        user = self.make_user()
        school_year = SchoolYearFactory(school__admin=user)

        with self.login(user):
            self.get_check_200("courses:create")

        form = self.get_context("form")
        assert form.school_year == school_year

    def test_school_year_uuid_bogus(self):
        """A malformed school year uuid in the querystring is ignored."""
        user = self.make_user()
        school_year = SchoolYearFactory(school__admin=user)

        with self.login(user):
            self.get_check_200("courses:create", data={"school_year": "bogus"})

        form = self.get_context("form")
        assert form.school_year == school_year

    def test_no_school_year(self):
        """When no school year is provided, the user is redirected to the list page."""
        user = self.make_user()

        with self.login(user):
            response = self.get("courses:create")

        self.response_302(response)
        assert self.reverse("schools:school_year_list") in response.get("Location")

    def test_has_grade_level(self):
        """A grade level put in the querystring is available as context."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school__admin=user)

        with self.login(user):
            self.get_check_200(
                "courses:create", data={"grade_level": str(grade_level.uuid)}
            )

        assert self.get_context("grade_level") == grade_level

    def test_not_other_grade_level(self):
        """A different user's grade level cannot be in the context."""
        user = self.make_user()
        SchoolYearFactory(school__admin=user)
        grade_level = GradeLevelFactory()

        with self.login(user):
            self.get_check_200(
                "courses:create", data={"grade_level": str(grade_level.uuid)}
            )

        assert self.get_context("grade_level") is None

    def test_bogus_grade_level(self):
        """A bogus grade level is ignored and not in the context"""
        user = self.make_user()
        SchoolYearFactory(school__admin=user)

        with self.login(user):
            self.get_check_200("courses:create", data={"grade_level": "bogus"})

        assert self.get_context("grade_level") is None

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        data = {
            "name": "Course name",
            "wednesday": "on",
            "friday": "on",
            "grade_levels": str(grade_level.id),
            "default_task_duration": 45,
        }

        with self.login(user):
            response = self.post("courses:create", data=data)

        course = Course.objects.get(grade_levels=grade_level.id)
        assert course.name == "Course name"
        assert course.days_of_week == Course.WEDNESDAY + Course.FRIDAY
        self.response_302(response)
        assert self.reverse("courses:detail", uuid=course.uuid) in response.get(
            "Location"
        )


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

        assert list(self.get_context("grade_levels")) == [grade_level]
        assert self.get_context("school_year") == grade_level.school_year
        assert self.get_context("course_tasks") == []
        assert self.get_context("last_task") is None

    def test_grade_level_name_with_task(self):
        """Any grade level specific task has the grade level's name next to it."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory(course=course, grade_level=grade_level)

        with self.login(user):
            self.get("courses:detail", uuid=course.uuid)

        self.assertResponseContains(grade_level.name)

    def test_last_task(self):
        """The last task is added to the context."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory(course=course)
        last_task = CourseTaskFactory(course=course)

        with self.login(user):
            self.get("courses:detail", uuid=course.uuid)

        assert self.get_context("last_task") == last_task


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
        data = {
            "name": "New course name",
            "wednesday": "on",
            "friday": "on",
            "grade_levels": str(grade_level.id),
            "default_task_duration": 45,
        }

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
        course = CourseFactory(grade_levels=[grade_level], default_task_duration=42)

        with self.login(user):
            self.get_check_200("courses:task_create", uuid=course.uuid)

        form = self.get_context("form")
        assert (
            form.get_initial_for_field(form.fields["duration"], "duration")
            == course.default_task_duration
        )

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

    def test_has_previous_task(self):
        """The previous task is in the context if the querystring is present."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)
        url = self.reverse("courses:task_create", uuid=course.uuid)
        url += f"?previous_task={task.uuid}"

        with self.login(user):
            self.get(url)

        assert self.get_context("previous_task") == task

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

    def test_has_grade_levels(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        other_grade_level = GradeLevelFactory(school_year=grade_level.school_year)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get("courses:task_create", uuid=course.uuid)

        grade_levels = set(self.get_context("grade_levels"))
        assert grade_levels == {grade_level, other_grade_level}

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


class TestBulkCreateCourseTasks(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:task_create_bulk", uuid=course.uuid)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level], default_task_duration=42)

        with self.login(user):
            self.get_check_200("courses:task_create_bulk", uuid=course.uuid)

        form = self.get_context("formset")[0]
        assert form.user == user
        assert (
            form.get_initial_for_field(form.fields["duration"], "duration")
            == course.default_task_duration
        )
        assert self.get_context("course") == course
        assert list(self.get_context("grade_levels")) == [grade_level]

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-course": str(course.id),
            "form-0-description": "A new task",
            "form-0-duration": "42",
        }

        with self.login(user):
            response = self.post(
                "courses:task_create_bulk", uuid=course.uuid, data=data
            )

        assert CourseTask.objects.count() == 1
        task = CourseTask.objects.get(course=course)
        assert task.description == data["form-0-description"]
        assert task.duration == int(data["form-0-duration"])
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "courses:detail", uuid=course.uuid
        )
        assert not hasattr(task, "graded_work")

    def test_after_task(self):
        """Tasks are placed after a specified task."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-course": str(course.id),
            "form-0-description": "A new task",
            "form-0-duration": "42",
            "form-1-course": str(course.id),
            "form-1-description": "Another new task",
            "form-1-duration": "42",
        }
        task_1 = CourseTaskFactory(course=course)
        task_2 = CourseTaskFactory(course=course)
        url = self.reverse("courses:task_create_bulk", uuid=course.uuid)
        url += f"?previous_task={task_1.uuid}"

        with self.login(user):
            self.post(url, data=data)

        task_3 = CourseTask.objects.get(description="A new task")
        task_4 = CourseTask.objects.get(description="Another new task")
        assert list(CourseTask.objects.all()) == [task_1, task_3, task_4, task_2]

    def test_redirect_next(self):
        """After creation, the user returns to the next URL."""
        next_url = "/another/location/"
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-course": str(course.id),
            "form-0-description": "A new task",
            "form-0-duration": "42",
        }
        url = self.reverse("courses:task_create_bulk", uuid=course.uuid)
        url += f"?next={next_url}"

        with self.login(user):
            response = self.post(url, data=data)

        self.response_302(response)
        assert next_url in response.get("Location")

    def test_has_previous_task(self):
        """When the previous task is in the querystring, it's in the context."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level], default_task_duration=42)
        task = CourseTaskFactory(course=course)
        url = self.reverse("courses:task_create_bulk", uuid=course.uuid)
        url += f"?previous_task={task.uuid}"

        with self.login(user):
            self.get_check_200(url)

        assert self.get_context("previous_task") == task


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

    def test_has_grade_levels(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        other_grade_level = GradeLevelFactory(school_year=grade_level.school_year)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)

        with self.login(user):
            self.get("courses:task_edit", uuid=task.uuid)

        grade_levels = set(self.get_context("grade_levels"))
        assert grade_levels == {grade_level, other_grade_level}

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


class TestCourseResourceCreateView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:resource_create", uuid=course.uuid)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("courses:resource_create", uuid=course.uuid)

        assert self.get_context("create")
        assert self.get_context("course") == course

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "course": str(course.id),
            "title": "Charlotte's Web",
            "details": "That's some pig.",
        }

        with self.login(user):
            response = self.post("courses:resource_create", uuid=course.uuid, data=data)

        assert CourseResource.objects.count() == 1
        resource = CourseResource.objects.get(course=course)
        assert resource.title == data["title"]
        assert resource.details == data["details"]
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "courses:detail", uuid=course.uuid
        )


class TestCourseResourceUpdateView(TestCase):
    def test_unauthenticated_access(self):
        resource = CourseResourceFactory()
        self.assertLoginRequired("courses:resource_edit", uuid=resource.uuid)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        resource = CourseResourceFactory(course__grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("courses:resource_edit", uuid=resource.uuid)

        assert not self.get_context("create")
        assert self.get_context("course") == resource.course

    def test_get_other_user(self):
        """A user may not edit another user's resource."""
        user = self.make_user()
        resource = CourseResourceFactory()

        with self.login(user):
            response = self.get("courses:resource_edit", uuid=resource.uuid)

        self.response_404(response)

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        resource = CourseResourceFactory(course__grade_levels=[grade_level])
        data = {
            "course": str(resource.course.id),
            "title": "Charlotte's Web",
            "details": "That's some pig.",
        }

        with self.login(user):
            response = self.post("courses:resource_edit", uuid=resource.uuid, data=data)

        assert CourseResource.objects.count() == 1
        resource = CourseResource.objects.get(course=resource.course)
        assert resource.title == data["title"]
        assert resource.details == data["details"]
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "courses:detail", uuid=resource.course.uuid
        )


class TestCourseResourceDeleteView(TestCase):
    def test_unauthenticated_access(self):
        resource = CourseResourceFactory()
        self.assertLoginRequired("courses:resource_delete", uuid=resource.uuid)

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        resource = CourseResourceFactory(course=course)

        with self.login(user):
            response = self.post("courses:resource_delete", uuid=resource.uuid)

        assert CourseResource.objects.count() == 0
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "courses:detail", uuid=course.uuid
        )

    def test_post_other_user(self):
        """A user may not delete another user's resource."""
        user = self.make_user()
        course = CourseFactory()
        resource = CourseResourceFactory(course=course)

        with self.login(user):
            response = self.get("courses:resource_delete", uuid=resource.uuid)

        self.response_404(response)
