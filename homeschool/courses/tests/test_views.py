import datetime
from unittest import mock

from waffle.testutils import override_flag

from homeschool.courses.models import Course, CourseResource, CourseTask, GradedWork
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseResourceFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.schools.tests.factories import GradeLevelFactory, SchoolYearFactory
from homeschool.students.tests.factories import (
    CourseworkFactory,
    EnrollmentFactory,
    GradeFactory,
)
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

    def test_school_year_id(self):
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
                "courses:create", data={"school_year": str(school_year.id)}
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
                "courses:create", data={"school_year": str(school_year.id)}
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

    def test_school_year_id_bogus(self):
        """A malformed school year id in the querystring is ignored."""
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
                "courses:create", data={"grade_level": str(grade_level.id)}
            )

        assert self.get_context("grade_level") == grade_level

    def test_not_other_grade_level(self):
        """A different user's grade level cannot be in the context."""
        user = self.make_user()
        SchoolYearFactory(school__admin=user)
        grade_level = GradeLevelFactory()

        with self.login(user):
            self.get_check_200(
                "courses:create", data={"grade_level": str(grade_level.id)}
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
            "is_active": False,
        }

        with self.login(user):
            response = self.post("courses:create", data=data)

        course = Course.objects.get(grade_levels=grade_level.id)
        assert course.name == "Course name"
        assert course.days_of_week == Course.WEDNESDAY + Course.FRIDAY
        self.response_302(response)
        assert self.reverse("courses:detail", pk=course.id) in response.get("Location")
        assert not course.is_active

    def test_course_copy_fills_form_fields(self):
        """The course to copy fills in the course form."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course_to_copy = CourseFactory(
            grade_levels=[grade_level], name="To Copy", default_task_duration=99
        )

        with self.login(user):
            self.get_check_200(
                "courses:create", data={"copy_from": str(course_to_copy.id)}
            )

        form = self.get_context("form")
        assert form.initial["name"] == "To Copy"
        assert form.initial["default_task_duration"] == 99

    def test_course_copy_only_user_courses(self):
        """A user cannot copy another user's course."""
        user = self.make_user()
        SchoolYearFactory(school=user.school)
        course_to_copy = CourseFactory()

        with self.login(user):
            self.get_check_200(
                "courses:create", data={"copy_from": str(course_to_copy.id)}
            )

        assert self.get_context("course_to_copy") is None

    def test_course_copy_tasks_resources(self):
        """Copying a course includes the tasks, graded work, and resources."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course_to_copy = CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory(course=course_to_copy)
        graded_task = CourseTaskFactory(course=course_to_copy)
        GradedWorkFactory(course_task=graded_task)
        CourseResourceFactory(course=course_to_copy)
        data = {
            "name": "Course name",
            "wednesday": "on",
            "friday": "on",
            "grade_levels": str(grade_level.id),
            "default_task_duration": 45,
        }
        url = self.reverse("courses:create")
        url += f"?copy_from={course_to_copy.id}"

        with self.login(user):
            self.post(url, data=data)

        assert Course.objects.count() == 2
        copied_course = Course.objects.last()
        assert copied_course.id != course_to_copy.id
        assert CourseTask.objects.filter(course=copied_course).count() == 2
        new_graded_task = CourseTask.objects.filter(course=copied_course).last()
        assert hasattr(new_graded_task, "graded_work")
        assert CourseResource.objects.filter(course=copied_course).count() == 1


class TestCourseDetailView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:detail", pk=course.id)

    @override_flag("combined_course_flag", active=True)
    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("courses:detail", pk=course.id)

        assert list(self.get_context("grade_levels")) == [grade_level]
        assert self.get_context("school_year") == grade_level.school_year
        assert self.get_context("course_tasks") == []
        assert self.get_context("last_task") is None
        self.assertInContext("task_details")

    def test_grade_level_name_with_task(self):
        """Any grade level specific task has the grade level's name next to it."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory(course=course, grade_level=grade_level)

        with self.login(user):
            self.get("courses:detail", pk=course.id)

        self.assertResponseContains(grade_level.name)

    def test_last_task(self):
        """The last task is added to the context."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory(course=course)
        last_task = CourseTaskFactory(course=course)

        with self.login(user):
            self.get("courses:detail", pk=course.id)

        assert self.get_context("last_task") == last_task

    def test_enrolled_students(self):
        """The enrolled students of the course are in the context."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        enrollment = EnrollmentFactory(grade_level=grade_level)

        with self.login(user):
            self.get_check_200("courses:detail", pk=course.id)

        assert self.get_context("enrolled_students") == [enrollment.student]

    @override_flag("combined_course_flag", active=True)
    def test_course_tasks_context(self):
        """All the task details of an enrolled student are in the context."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)
        enrollment = EnrollmentFactory(grade_level=grade_level)
        work = CourseworkFactory(student=enrollment.student, course_task=task)
        grade = GradeFactory(student=enrollment.student, graded_work__course_task=task)
        url = self.reverse("courses:detail", pk=course.id) + "?completed_tasks=1"

        with self.login(user):
            self.get_check_200(url)

        assert self.get_context("task_details") == [
            {
                "number": 1,
                "task": task,
                "complete": True,
                "student_details": [
                    {
                        "student": enrollment.student,
                        "assigned": True,
                        "coursework": work,
                        "grade": grade,
                        "planned_date": None,
                    }
                ],
            }
        ]

    @override_flag("combined_course_flag", active=True)
    def test_task_complete_no_student(self):
        """When there are no students, a task defaults to incomplete."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        CourseTaskFactory(course=course)

        with self.login(user):
            self.get_check_200("courses:detail", pk=course.id)

        detail = self.get_context("task_details")[0]
        assert not detail["complete"]

    @override_flag("combined_course_flag", active=True)
    def test_task_complete_one_student_coursework(self):
        """When a student has not completed, the task is marked incomplete."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)
        EnrollmentFactory(grade_level=grade_level)
        enrollment = EnrollmentFactory(grade_level=grade_level)
        CourseworkFactory(student=enrollment.student, course_task=task)

        with self.login(user):
            self.get_check_200("courses:detail", pk=course.id)

        detail = self.get_context("task_details")[0]
        assert not detail["complete"]

    @override_flag("combined_course_flag", active=True)
    def test_task_complete_both_students_done(self):
        """When all students are done with a task, it is marked complete."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)
        enrollment_1 = EnrollmentFactory(grade_level=grade_level)
        CourseworkFactory(student=enrollment_1.student, course_task=task)
        enrollment_2 = EnrollmentFactory(grade_level=grade_level)
        CourseworkFactory(student=enrollment_2.student, course_task=task)
        url = self.reverse("courses:detail", pk=course.id) + "?completed_tasks=1"

        with self.login(user):
            self.get_check_200(url)

        detail = self.get_context("task_details")[0]
        assert detail["complete"]

    @override_flag("combined_course_flag", active=True)
    def test_hide_complete_tasks(self):
        """With students enrolled, completed tasks are hidden by default."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)
        enrollment = EnrollmentFactory(grade_level=grade_level)
        CourseworkFactory(student=enrollment.student, course_task=task)

        with self.login(user):
            self.get_check_200("courses:detail", pk=course.id)

        assert not self.get_context("task_details")


class TestCourseEditView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:edit", pk=course.id)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("courses:edit", pk=course.id)

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
            "is_active": False,
        }

        with self.login(user):
            self.post("courses:edit", pk=course.id, data=data)

        course.refresh_from_db()
        assert course.name == "New course name"
        assert course.days_of_week == Course.WEDNESDAY + Course.FRIDAY
        assert not course.is_active


class TestCourseDeleteView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:delete", pk=course.id)

    def test_other_course(self):
        """A user may not access another user's course."""
        user = self.make_user()
        course = CourseFactory()

        with self.login(user):
            response = self.get("courses:delete", pk=course.id)

        assert response.status_code == 404

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)
        GradeFactory(graded_work__course_task=task)
        CourseworkFactory(course_task=task)
        CourseResourceFactory(course=course)

        with self.login(user):
            self.get_check_200("courses:delete", pk=course.id)

        assert self.get_context("tasks_count") == 1
        assert self.get_context("grades_count") == 1
        assert self.get_context("coursework_count") == 1
        assert self.get_context("course_resources_count") == 1

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            response = self.post("courses:delete", pk=course.id)

        assert Course.objects.count() == 0
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", pk=grade_level.school_year.id
        )


class TestCourseCopySelectView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("courses:copy")

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("courses:copy")

        assert self.get_context("school_years") == [
            {
                "school_year": grade_level.school_year,
                "grade_levels": {grade_level: [course]},
            }
        ]

    def test_only_user_courses(self):
        """The copy view only lists the user's courses."""
        user = self.make_user()
        CourseFactory()

        with self.login(user):
            self.get_check_200("courses:copy")

        assert self.get_context("school_years") == []


class TestCourseTaskCreateView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:task_create", pk=course.id)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level], default_task_duration=42)

        with self.login(user):
            self.get_check_200("courses:task_create", pk=course.id)

        form = self.get_context("form")
        assert form.initial["duration"] == course.default_task_duration

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {"course": str(course.id), "description": "A new task", "duration": "30"}

        with self.login(user):
            response = self.post("courses:task_create", pk=course.id, data=data)

        assert CourseTask.objects.count() == 1
        task = CourseTask.objects.get(course=course)
        assert task.description == data["description"]
        assert task.duration == int(data["duration"])
        self.response_302(response)
        assert response.get("Location") == self.reverse("courses:detail", pk=course.id)
        assert not hasattr(task, "graded_work")

    def test_has_previous_task(self):
        """The previous task is in the context if the querystring is present."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)
        url = self.reverse("courses:task_create", pk=course.id)
        url += f"?previous_task={task.id}"

        with self.login(user):
            self.get(url)

        assert self.get_context("previous_task") == task

    def test_has_create(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get("courses:task_create", pk=course.id)

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
        url = self.reverse("courses:task_create", pk=course.id)
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
            self.get("courses:task_create", pk=course.id)

        self.assertContext("course", course)

    def test_has_grade_levels(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        other_grade_level = GradeLevelFactory(school_year=grade_level.school_year)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get("courses:task_create", pk=course.id)

        grade_levels = set(self.get_context("grade_levels"))
        assert grade_levels == {grade_level, other_grade_level}

    def test_after_task(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {"course": str(course.id), "description": "A new task", "duration": "30"}
        task_1 = CourseTaskFactory(course=course)
        task_2 = CourseTaskFactory(course=course)
        url = self.reverse("courses:task_create", pk=course.id)
        url += f"?previous_task={task_1.id}"

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
            self.post("courses:task_create", pk=course.id, data=data)

        assert CourseTask.objects.count() == 1
        task = CourseTask.objects.get(course=course)
        assert task.graded_work is not None

    def test_replicates(self):
        """A user that replicates data will create multiple tasks."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "course": str(course.id),
            "description": "A new task",
            "duration": "30",
            "replicate": "on",
            "replicate_count": "2",
        }

        with self.login(user):
            self.post("courses:task_create", pk=course.id, data=data)

        assert CourseTask.objects.count() == 2
        descriptions = list(
            CourseTask.objects.filter(course=course).values_list(
                "description", flat=True
            )
        )
        assert descriptions == ["A new task", "A new task"]

    def test_bad_replicate_count(self):
        """A bad replicate count does no harm."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "course": str(course.id),
            "description": "A new task",
            "duration": "30",
            "replicate": "on",
            "replicate_count": "bad",
        }

        with self.login(user):
            self.post("courses:task_create", pk=course.id, data=data)

        assert CourseTask.objects.count() == 1

    @mock.patch("homeschool.courses.views.schools_constants")
    def test_max_allowed_enforced(self, mock_constants):
        """When replicate count is higher than the max, only the max are created."""
        mock_constants.MAX_ALLOWED_DAYS = 2
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "course": str(course.id),
            "description": "A new task",
            "duration": "30",
            "replicate": "on",
            "replicate_count": "10",
        }

        with self.login(user):
            self.post("courses:task_create", pk=course.id, data=data)

        assert CourseTask.objects.count() == 2

    def test_replicates_with_autonumber(self):
        """A user who replicates with autonumber will create multiple numbered tasks."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        data = {
            "course": str(course.id),
            "description": "A new task",
            "duration": "30",
            "replicate": "on",
            "replicate_count": "2",
            "autonumber": "on",
        }

        with self.login(user):
            self.post("courses:task_create", pk=course.id, data=data)

        assert CourseTask.objects.count() == 2
        descriptions = list(
            CourseTask.objects.filter(course=course).values_list(
                "description", flat=True
            )
        )
        assert descriptions == ["A new task 1", "A new task 2"]


class TestBulkCreateCourseTasks(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:task_create_bulk", pk=course.id)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level], default_task_duration=42)

        with self.login(user):
            self.get_check_200("courses:task_create_bulk", pk=course.id)

        form = self.get_context("formset")[0]
        assert form.user == user
        assert (
            form.get_initial_for_field(form.fields["duration"], "duration")
            == course.default_task_duration
        )
        assert self.get_context("course") == course
        assert list(self.get_context("grade_levels")) == [grade_level]
        assert self.get_context("extra_forms") == "3"

    def test_other_course(self):
        """A user may not bulk create for another user's course."""
        user = self.make_user()
        course = CourseFactory()

        with self.login(user):
            response = self.get("courses:task_create_bulk", pk=course.id)

        assert response.status_code == 404

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
            response = self.post("courses:task_create_bulk", pk=course.id, data=data)

        assert CourseTask.objects.count() == 1
        task = CourseTask.objects.get(course=course)
        assert task.description == data["form-0-description"]
        assert task.duration == int(data["form-0-duration"])
        self.response_302(response)
        assert response.get("Location") == self.reverse("courses:detail", pk=course.id)
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
        url = self.reverse("courses:task_create_bulk", pk=course.id)
        url += f"?previous_task={task_1.id}"

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
        url = self.reverse("courses:task_create_bulk", pk=course.id)
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
        url = self.reverse("courses:task_create_bulk", pk=course.id)
        url += f"?previous_task={task.id}"

        with self.login(user):
            self.get_check_200(url)

        assert self.get_context("previous_task") == task


class TestGetCourseTaskBulkHx(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired(
            "courses:task_create_bulk_hx", pk=course.id, last_form_number=42
        )

    def test_other_course(self):
        """A user may not get bulk create forms for another user's course."""
        user = self.make_user()
        course = CourseFactory()

        with self.login(user):
            response = self.get(
                "courses:task_create_bulk_hx", pk=course.id, last_form_number=2
            )

        assert response.status_code == 404

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level], default_task_duration=42)

        with self.login(user):
            self.get_check_200(
                "courses:task_create_bulk_hx", pk=course.id, last_form_number=2
            )

        assert len(self.get_context("forms")) == 3
        form = self.get_context("forms")[0]
        assert form.user == user
        assert (
            form.get_initial_for_field(form.fields["duration"], "duration")
            == course.default_task_duration
        )
        assert self.get_context("course") == course
        assert list(self.get_context("grade_levels")) == [grade_level]
        assert self.get_context("last_form_number") == 2


class TestCourseTaskUpdateView(TestCase):
    def test_unauthenticated_access(self):
        task = CourseTaskFactory()
        self.assertLoginRequired("courses:task_edit", pk=task.id)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)

        with self.login(user):
            self.get_check_200("courses:task_edit", pk=task.id)

    def test_get_other_user(self):
        user = self.make_user()
        task = CourseTaskFactory()

        with self.login(user):
            response = self.get("courses:task_edit", pk=task.id)

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
            response = self.post("courses:task_edit", pk=task.id, data=data)

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
            self.get("courses:task_edit", pk=task.id)

        self.assertContext("course", task.course)

    def test_has_grade_levels(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        other_grade_level = GradeLevelFactory(school_year=grade_level.school_year)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)

        with self.login(user):
            self.get("courses:task_edit", pk=task.id)

        grade_levels = set(self.get_context("grade_levels"))
        assert grade_levels == {grade_level, other_grade_level}

    def test_has_previous_task(self):
        """A previous task is in the context when it exists."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        previous_task = CourseTaskFactory(course=course)
        task = CourseTaskFactory(course=course)

        with self.login(user):
            self.get("courses:task_edit", pk=task.id)

        assert self.get_context("previous_task") == previous_task

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
        url = self.reverse("courses:task_edit", pk=task.id)
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
            self.post("courses:task_edit", pk=task.id, data=data)

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
            self.post("courses:task_edit", pk=task.id, data=data)

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
            self.post("courses:task_edit", pk=task.id, data=data)

        task.refresh_from_db()
        assert not hasattr(task, "graded_work")


class TestCourseTaskDeleteView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        task = CourseTaskFactory(course=course)
        self.assertLoginRequired("courses:task_delete", course_id=course.id, pk=task.id)

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)

        with self.login(user):
            response = self.post("courses:task_delete", course_id=course.id, pk=task.id)

        assert CourseTask.objects.count() == 0
        self.response_302(response)
        assert response.get("Location") == self.reverse("courses:detail", pk=course.id)

    def test_post_other_user(self):
        user = self.make_user()
        course = CourseFactory()
        task = CourseTaskFactory(course=course)

        with self.login(user):
            response = self.get("courses:task_delete", course_id=course.id, pk=task.id)

        self.response_404(response)

    def test_redirect_next(self):
        """The delete view redirects to next parameter if present."""
        next_url = "/another/location/"
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)
        url = self.reverse("courses:task_delete", course_id=course.id, pk=task.id)
        url += f"?next={next_url}"

        with self.login(user):
            response = self.post(url)

        self.response_302(response)
        assert next_url in response.get("Location")


class TestCourseTaskHxDeleteView(TestCase):
    def test_unauthenticated_access(self):
        task = CourseTaskFactory()
        self.assertLoginRequired("courses:task_hx_delete", pk=task.id)

    @override_flag("combined_course_flag", active=True)
    def test_delete(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        task = CourseTaskFactory(course=course)

        with self.login(user):
            response = self.delete("courses:task_hx_delete", pk=task.id)

        assert CourseTask.objects.count() == 0
        self.response_200(response)
        assert "task_details" in response.context

    def test_delete_other_user(self):
        """Another user cannot delete a user's task."""
        user = self.make_user()
        course = CourseFactory()
        task = CourseTaskFactory(course=course)

        with self.login(user):
            response = self.delete("courses:task_hx_delete", pk=task.id)

        assert CourseTask.objects.count() == 1
        self.response_404(response)


class TestCourseTaskDown(TestCase):
    def test_unauthenticated_access(self):
        task = CourseTaskFactory()
        self.assertLoginRequired("courses:task_down", pk=task.id)

    def test_post(self):
        """A task is moved down."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        first_task = CourseTaskFactory(course=course)
        second_task = CourseTaskFactory(course=course)

        with self.login(user):
            response = self.post("courses:task_down", pk=first_task.id)

        assert (
            response.get("Location")
            == self.reverse("courses:detail", first_task.course.id)
            + f"#task-{first_task.id}"
        )
        assert list(CourseTask.objects.all()) == [second_task, first_task]


class TestCourseTaskUp(TestCase):
    def test_unauthenticated_access(self):
        task = CourseTaskFactory()
        self.assertLoginRequired("courses:task_up", pk=task.id)

    def test_post(self):
        """A task is moved up."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        first_task = CourseTaskFactory(course=course)
        second_task = CourseTaskFactory(course=course)

        with self.login(user):
            response = self.post("courses:task_up", pk=second_task.id)

        assert (
            response.get("Location")
            == self.reverse("courses:detail", second_task.course.id)
            + f"#task-{second_task.id}"
        )
        assert list(CourseTask.objects.all()) == [second_task, first_task]


class TestCourseResourceCreateView(TestCase):
    def test_unauthenticated_access(self):
        course = CourseFactory()
        self.assertLoginRequired("courses:resource_create", pk=course.id)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("courses:resource_create", pk=course.id)

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
            response = self.post("courses:resource_create", pk=course.id, data=data)

        assert CourseResource.objects.count() == 1
        resource = CourseResource.objects.get(course=course)
        assert resource.title == data["title"]
        assert resource.details == data["details"]
        self.response_302(response)
        assert response.get("Location") == self.reverse("courses:detail", pk=course.id)


class TestCourseResourceUpdateView(TestCase):
    def test_unauthenticated_access(self):
        resource = CourseResourceFactory()
        self.assertLoginRequired("courses:resource_edit", pk=resource.id)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        resource = CourseResourceFactory(course__grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("courses:resource_edit", pk=resource.id)

        assert not self.get_context("create")
        assert self.get_context("course") == resource.course

    def test_get_other_user(self):
        """A user may not edit another user's resource."""
        user = self.make_user()
        resource = CourseResourceFactory()

        with self.login(user):
            response = self.get("courses:resource_edit", pk=resource.id)

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
            response = self.post("courses:resource_edit", pk=resource.id, data=data)

        assert CourseResource.objects.count() == 1
        resource = CourseResource.objects.get(course=resource.course)
        assert resource.title == data["title"]
        assert resource.details == data["details"]
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "courses:detail", pk=resource.course.id
        )


class TestCourseResourceDeleteView(TestCase):
    def test_unauthenticated_access(self):
        resource = CourseResourceFactory()
        self.assertLoginRequired("courses:resource_delete", pk=resource.id)

    def test_post(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        course = CourseFactory(grade_levels=[grade_level])
        resource = CourseResourceFactory(course=course)

        with self.login(user):
            response = self.post("courses:resource_delete", pk=resource.id)

        assert CourseResource.objects.count() == 0
        self.response_302(response)
        assert response.get("Location") == self.reverse("courses:detail", pk=course.id)

    def test_post_other_user(self):
        """A user may not delete another user's resource."""
        user = self.make_user()
        course = CourseFactory()
        resource = CourseResourceFactory(course=course)

        with self.login(user):
            response = self.post("courses:resource_delete", pk=resource.id)

        self.response_404(response)
