import datetime

from homeschool.courses.tests.factories import CourseFactory, CourseResourceFactory
from homeschool.schools.models import GradeLevel, SchoolBreak, SchoolYear
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolBreakFactory,
    SchoolYearFactory,
)
from homeschool.students.tests.factories import (
    EnrollmentFactory,
    GradeFactory,
    StudentFactory,
)
from homeschool.test import TestCase


class TestCurrentSchoolYearView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("schools:current_school_year")

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:current_school_year")

        assert school_year == self.get_context("schoolyear")

    def test_future_school_year(self):
        """Go to a future school year if there is no current one.

        The user may be new and have no currently active school year.
        It would be pretty lame to send them to the list
        when they may be building out their first school year.
        """
        user = self.make_user()
        today = user.get_local_today()
        school_year = SchoolYearFactory(
            school=user.school,
            start_date=today + datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=200),
        )

        with self.login(user):
            self.get_check_200("schools:current_school_year")

        assert school_year == self.get_context("schoolyear")

    def test_no_current_school_year(self):
        """With no current school year, the user sees the school year list page."""
        user = self.make_user()

        with self.login(user):
            response = self.get("schools:current_school_year")

        self.response_302(response)
        assert self.reverse("schools:school_year_list") in response.get("Location")

    def test_only_school_year_for_user(self):
        """A user may only view their own school years."""
        user = self.make_user()
        SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:current_school_year")

        self.response_302(response)


class TestSchoolYearDetailView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("schools:school_year_detail", uuid=school_year.uuid)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:school_year_detail", uuid=school_year.uuid)

        assert self.get_context("is_in_school_year")
        assert self.get_context("enroll_url") == self.reverse(
            "students:enrollment_create", school_year_uuid=school_year.uuid
        )

    def test_only_school_year_for_user(self):
        """A user may only view their own school years."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:school_year_detail", uuid=school_year.uuid)

        self.response_404(response)

    def test_show_all_months(self):
        """When the option is provided, the page shows all calendar months."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200(
                "schools:school_year_detail",
                uuid=school_year.uuid,
                data={"show_all_months": "1"},
            )

        assert len(self.get_context("calendar")["months"]) == 13

    def test_grade_level_info(self):
        """The context has the grade level structure expected by the template."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            self.get_check_200("schools:school_year_detail", uuid=school_year.uuid)

        assert self.get_context("grade_levels") == [
            {"grade_level": grade_level, "courses": [course]}
        ]

    def test_no_enroll_url(self):
        """When enrollment is full, do not show the enroll button."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        student = StudentFactory(school=user.school)
        EnrollmentFactory(student=student, grade_level__school_year=school_year)

        with self.login(user):
            self.get_check_200("schools:school_year_detail", uuid=school_year.uuid)

        assert self.get_context("enroll_url") is None

    def test_more_enrollable(self):
        """When more students can be enrolled, show the enroll button."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        StudentFactory(school=user.school)
        student = StudentFactory(school=user.school)
        EnrollmentFactory(student=student, grade_level__school_year=school_year)

        with self.login(user):
            self.get_check_200("schools:school_year_detail", uuid=school_year.uuid)

        assert self.get_context("enroll_url") == self.reverse(
            "students:enrollment_create", school_year_uuid=school_year.uuid
        )


class TestSchoolYearCreateView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("schools:school_year_create")

    def test_get(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("schools:school_year_create")

    def test_has_create(self):
        """The create view has a create boolean in context."""
        user = self.make_user()

        with self.login(user):
            self.get("schools:school_year_create")

        self.assertContext("create", True)

    def test_post(self):
        """A user can create a school year."""
        user = self.make_user()
        data = {
            "school": str(user.school.id),
            "start_date": "1/1/20",
            "end_date": "12/31/20",
            "monday": True,
        }

        with self.login(user):
            response = self.post("schools:school_year_create", data=data)

        school_year = SchoolYear.objects.get(school=user.school)
        assert school_year.days_of_week == SchoolYear.MONDAY
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", uuid=school_year.uuid
        )


class TestSchoolYearEditView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("schools:school_year_edit", uuid=school_year.uuid)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:school_year_edit", uuid=school_year.uuid)

    def test_only_school_year_for_user(self):
        """A user may only edit their own school years."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:school_year_edit", uuid=school_year.uuid)

        self.response_404(response)

    def test_post(self):
        """A user can update the school year."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        new_start_date = school_year.start_date - datetime.timedelta(days=1)
        data = {
            "school": str(school_year.school.id),
            "start_date": str(new_start_date),
            "end_date": str(school_year.end_date),
            "wednesday": "on",
            "friday": "on",
        }

        with self.login(user):
            response = self.post(
                "schools:school_year_edit", uuid=school_year.uuid, data=data
            )

        school_year.refresh_from_db()
        assert school_year.start_date == new_start_date
        assert school_year.days_of_week == SchoolYear.WEDNESDAY + SchoolYear.FRIDAY
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", uuid=school_year.uuid
        )


class TestSchoolYearListView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("schools:school_year_list")

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:school_year_list")

        assert school_year in self.get_context("schoolyear_list")

    def test_only_school_year_for_user(self):
        """A user may only view their own school years."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            self.get("schools:school_year_list")

        assert school_year not in self.get_context("schoolyear_list")


class TestGradeLevelCreateView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("schools:grade_level_create", uuid=school_year.uuid)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:grade_level_create", uuid=school_year.uuid)

        assert school_year == self.get_context("school_year")

    def test_post(self):
        """A user can create a grade level for their school year."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        data = {"school_year": str(school_year.id), "name": "3rd Grade"}

        with self.login(user):
            response = self.post(
                "schools:grade_level_create", uuid=school_year.uuid, data=data
            )

        grade_level = GradeLevel.objects.get(school_year=school_year)
        assert grade_level.name == "3rd Grade"
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", uuid=school_year.uuid
        )

    def test_not_found_for_other_school(self):
        """A user cannot add a grade level to another user's school year."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:grade_level_create", uuid=school_year.uuid)

        self.response_404(response)


class TestSchoolBreakCreateView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("schools:school_break_create", uuid=school_year.uuid)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:school_break_create", uuid=school_year.uuid)

        assert self.get_context("school_year") == school_year
        assert self.get_context("create")

    def test_post(self):
        """A user can create a school break for their school year."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        data = {
            "school_year": str(school_year.id),
            "description": "Christmas",
            "start_date": str(school_year.start_date),
            "end_date": str(school_year.start_date),
        }

        with self.login(user):
            response = self.post(
                "schools:school_break_create", uuid=school_year.uuid, data=data
            )

        school_break = SchoolBreak.objects.get(school_year=school_year)
        assert school_break.description == "Christmas"
        assert school_break.start_date == school_year.start_date
        assert school_break.end_date == school_year.start_date
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", uuid=school_year.uuid
        )

    def test_not_found_for_other_school(self):
        """A user cannot add a school break to another user's school year."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:school_break_create", uuid=school_year.uuid)

        self.response_404(response)

    def test_no_school(self):
        """A missing school is an error."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        data = {
            "school_day": "0",
            "description": "Christmas",
            "start_date": "2020-08-05",
            "end_date": "2020-08-05",
        }

        with self.login(user):
            response = self.post(
                "schools:school_break_create", uuid=school_year.uuid, data=data
            )

        form = self.get_context("form")
        assert form.non_field_errors() == ["Invalid school year."]
        self.response_200(response)

    def test_no_other_school_post(self):
        """A user may not create a school break with data from another school."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        another_school_year = SchoolYearFactory()
        data = {
            "school_year": str(another_school_year.id),
            "description": "Christmas",
            "start_date": "2020-08-05",
            "end_date": "2020-08-05",
        }

        with self.login(user):
            response = self.post(
                "schools:school_break_create", uuid=school_year.uuid, data=data
            )

        form = self.get_context("form")
        assert form.non_field_errors() == [
            "A school break cannot be created for a different user's school year."
        ]
        self.response_200(response)


class TestSchoolBreakUpdateView(TestCase):
    def test_unauthenticated_access(self):
        school_break = SchoolBreakFactory()
        self.assertLoginRequired("schools:school_break_edit", uuid=school_break.uuid)

    def test_get(self):
        user = self.make_user()
        school_break = SchoolBreakFactory(school_year__school=user.school)

        with self.login(user):
            self.get_check_200("schools:school_break_edit", uuid=school_break.uuid)

        assert self.get_context("school_year") == school_break.school_year

    def test_post(self):
        """A user can update a school break for their school year."""
        user = self.make_user()
        school_break = SchoolBreakFactory(school_year__school=user.school)
        data = {
            "school_year": str(school_break.school_year.id),
            "description": "Christmas",
            "start_date": str(school_break.school_year.start_date),
            "end_date": str(school_break.school_year.start_date),
        }

        with self.login(user):
            response = self.post(
                "schools:school_break_edit", uuid=school_break.uuid, data=data
            )

        school_break.refresh_from_db()
        assert school_break.description == "Christmas"
        assert school_break.start_date == school_break.school_year.start_date
        assert school_break.end_date == school_break.school_year.start_date
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", uuid=school_break.school_year.uuid
        )

    def test_only_users_breaks(self):
        """A user can only edit their own school breaks."""
        user = self.make_user()
        school_break = SchoolBreakFactory()

        with self.login(user):
            response = self.get("schools:school_break_edit", uuid=school_break.uuid)

        self.response_404(response)


class TestSchoolBreakDeleteView(TestCase):
    def test_unauthenticated_access(self):
        school_break = SchoolBreakFactory()
        self.assertLoginRequired("schools:school_break_delete", uuid=school_break.uuid)

    def test_post(self):
        user = self.make_user()
        school_break = SchoolBreakFactory(school_year__school=user.school)

        with self.login(user):
            response = self.post("schools:school_break_delete", uuid=school_break.uuid)

        assert SchoolBreak.objects.count() == 0
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", uuid=school_break.school_year.uuid
        )

    def test_post_other_user(self):
        """A user may not delete another user's break."""
        user = self.make_user()
        school_break = SchoolBreakFactory()

        with self.login(user):
            response = self.post("schools:school_break_delete", uuid=school_break.uuid)

        self.response_404(response)


class TestReportsIndex(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("reports:index")

    def test_get(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("reports:index")

    def test_has_enrollments(self):
        """The enrollments are in the context."""
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)

        with self.login(user):
            self.get_check_200("reports:index")

        assert list(self.get_context("enrollments")) == [enrollment]

    def test_no_other_enrollments(self):
        """Another user's enrollments are not in the context."""
        user = self.make_user()
        EnrollmentFactory()

        with self.login(user):
            self.get_check_200("reports:index")

        assert list(self.get_context("enrollments")) == []


class TestProgressReportView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        student = StudentFactory()
        self.assertLoginRequired(
            "reports:progress", uuid=school_year.uuid, student_uuid=student.uuid
        )

    def test_get(self):
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)

        with self.login(user):
            self.get_check_200(
                "reports:progress",
                uuid=enrollment.grade_level.school_year.uuid,
                student_uuid=enrollment.student.uuid,
            )

        assert self.get_context("grade_level") == enrollment.grade_level
        assert self.get_context("school_year") == enrollment.grade_level.school_year
        assert self.get_context("student") == enrollment.student

    def test_not_found_for_other_school(self):
        """A user cannot access a progress report that is not from their school."""
        user = self.make_user()
        enrollment = EnrollmentFactory()

        with self.login(user):
            response = self.get(
                "reports:progress",
                uuid=enrollment.grade_level.school_year.uuid,
                student_uuid=enrollment.student.uuid,
            )

        self.response_404(response)

    def test_only_students_grades(self):
        """Only grades from the student are included."""
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)
        grade = GradeFactory(
            student=enrollment.student,
            graded_work__course_task__course__grade_levels=[enrollment.grade_level],
        )
        GradeFactory(
            graded_work__course_task__course__grade_levels=[enrollment.grade_level]
        )

        with self.login(user):
            self.get_check_200(
                "reports:progress",
                uuid=enrollment.grade_level.school_year.uuid,
                student_uuid=enrollment.student.uuid,
            )

        assert list(self.get_context("grades")) == [grade]


class TestResourceReportView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        student = StudentFactory()
        self.assertLoginRequired(
            "reports:resource", uuid=school_year.uuid, student_uuid=student.uuid
        )

    def test_get(self):
        user = self.make_user()
        enrollment = EnrollmentFactory(grade_level__school_year__school=user.school)
        course = CourseFactory(grade_levels=[enrollment.grade_level])
        resource = CourseResourceFactory(course=course)

        with self.login(user):
            self.get_check_200(
                "reports:resource",
                uuid=enrollment.grade_level.school_year.uuid,
                student_uuid=enrollment.student.uuid,
            )

        assert self.get_context("grade_level") == enrollment.grade_level
        assert self.get_context("school_year") == enrollment.grade_level.school_year
        assert self.get_context("student") == enrollment.student
        assert list(self.get_context("resources")) == [resource]

    def test_not_found_for_other_school(self):
        """A user cannot access a progress report that is not from their school."""
        user = self.make_user()
        enrollment = EnrollmentFactory()

        with self.login(user):
            response = self.get(
                "reports:resource",
                uuid=enrollment.grade_level.school_year.uuid,
                student_uuid=enrollment.student.uuid,
            )

        self.response_404(response)
