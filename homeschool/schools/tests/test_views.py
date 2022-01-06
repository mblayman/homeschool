import datetime

from homeschool.courses.models import Course
from homeschool.courses.tests.factories import CourseFactory
from homeschool.schools.models import GradeLevel, SchoolBreak, SchoolYear
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolBreakFactory,
    SchoolYearFactory,
)
from homeschool.students.tests.factories import CourseworkFactory, EnrollmentFactory
from homeschool.test import TestCase


class TestCurrentSchoolYearView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("schools:current_school_year")

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:current_school_year")

        assert self.get_context("nav_link") == "school_year"
        assert self.get_context("schoolyear") == school_year

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
        self.assertLoginRequired("schools:school_year_detail", pk=school_year.id)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:school_year_detail", pk=school_year.id)

        assert self.get_context("nav_link") == "school_year"
        assert self.get_context("is_in_school_year")

    def test_only_school_year_for_user(self):
        """A user may only view their own school years."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:school_year_detail", pk=school_year.id)

        self.response_404(response)

    def test_show_all_months(self):
        """When the option is provided, the page shows all calendar months."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200(
                "schools:school_year_detail",
                pk=school_year.id,
                data={"show_all_months": "1"},
            )

        assert len(self.get_context("calendar")["months"]) == 13

    def test_grade_level_info(self):
        """The context has the grade level structure expected by the template."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(grade_levels=[grade_level])
        EnrollmentFactory(grade_level=grade_level)

        with self.login(user):
            self.get_check_200("schools:school_year_detail", pk=school_year.id)

        assert self.get_context("grade_levels") == [
            {"grade_level": grade_level, "courses": [course], "has_students": True}
        ]


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
            "schools:school_year_detail", pk=school_year.id
        )


class TestSchoolYearEditView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("schools:school_year_edit", pk=school_year.id)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:school_year_edit", pk=school_year.id)

    def test_only_school_year_for_user(self):
        """A user may only edit their own school years."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:school_year_edit", pk=school_year.id)

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
                "schools:school_year_edit", pk=school_year.id, data=data
            )

        school_year.refresh_from_db()
        assert school_year.start_date == new_start_date
        assert school_year.days_of_week == SchoolYear.WEDNESDAY + SchoolYear.FRIDAY
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", pk=school_year.id
        )


class TestSchoolYearForecastView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("schools:school_year_forecast", pk=school_year.id)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        enrollment = EnrollmentFactory(grade_level__school_year=school_year)
        course = CourseFactory(
            grade_levels=[enrollment.grade_level], days_of_week=Course.ALL_DAYS
        )
        coursework = CourseworkFactory(course_task__course=course)

        with self.login(user):
            self.get_check_200("schools:school_year_forecast", pk=school_year.id)

        assert self.get_context("schoolyear") == school_year
        assert self.get_context("students") == [
            {
                "student": enrollment.student,
                "courses": [
                    {"course": course, "last_forecast_date": coursework.completed_date}
                ],
            }
        ]

    def test_not_found_for_other_school(self):
        """A user cannot view the forecast of another user's school year."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:school_year_forecast", pk=school_year.id)

        self.response_404(response)


class TestSchoolYearListView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("schools:school_year_list")

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:school_year_list")

        assert self.get_context("nav_link") == "school_year"
        assert school_year in self.get_context("schoolyear_list")

    def test_only_school_year_for_user(self):
        """A user may only view their own school years."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            self.get("schools:school_year_list")

        assert school_year not in self.get_context("schoolyear_list")


class TestGradeLevelDetailView(TestCase):
    def test_unauthenticated_access(self):
        grade_level = GradeLevelFactory()
        self.assertLoginRequired("schools:grade_level_detail", pk=grade_level.id)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        enrollment = EnrollmentFactory(
            student__school=user.school, grade_level=grade_level
        )

        with self.login(user):
            self.get_check_200("schools:grade_level_detail", pk=grade_level.id)

        assert self.get_context("school_year") == grade_level.school_year
        assert list(self.get_context("enrollments")) == [enrollment]
        assert not self.get_context("show_enroll_cta")

    def test_only_users_grade_levels(self):
        """A user can only view their own grade levels."""
        user = self.make_user()
        grade_level = GradeLevelFactory()

        with self.login(user):
            response = self.get("schools:grade_level_detail", pk=grade_level.id)

        self.response_404(response)


class TestGradeLevelCreateView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("schools:grade_level_create", pk=school_year.id)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)

        with self.login(user):
            self.get_check_200("schools:grade_level_create", pk=school_year.id)

        assert school_year == self.get_context("school_year")
        assert self.get_context("create")

    def test_post(self):
        """A user can create a grade level for their school year."""
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        data = {"school_year": str(school_year.id), "name": "3rd Grade"}

        with self.login(user):
            response = self.post(
                "schools:grade_level_create", pk=school_year.id, data=data
            )

        grade_level = GradeLevel.objects.get(school_year=school_year)
        assert grade_level.name == "3rd Grade"
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", pk=school_year.id
        )

    def test_not_found_for_other_school(self):
        """A user cannot add a grade level to another user's school year."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:grade_level_create", pk=school_year.id)

        self.response_404(response)


class TestGradeLevelUpdateView(TestCase):
    def test_unauthenticated_access(self):
        grade_level = GradeLevelFactory()
        self.assertLoginRequired("schools:grade_level_edit", pk=grade_level.id)

    def test_get(self):
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)

        with self.login(user):
            self.get_check_200("schools:grade_level_edit", pk=grade_level.id)

        assert self.get_context("school_year") == grade_level.school_year

    def test_post(self):
        """A user can update a grade level for their school year."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        data = {"school_year": str(grade_level.school_year.id), "name": "12th Grade"}

        with self.login(user):
            response = self.post(
                "schools:grade_level_edit", pk=grade_level.id, data=data
            )

        grade_level.refresh_from_db()
        assert grade_level.name == "12th Grade"
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", pk=grade_level.school_year.id
        )

    def test_only_users_grade_levels(self):
        """A user can only edit their own grade levels."""
        user = self.make_user()
        grade_level = GradeLevelFactory()

        with self.login(user):
            response = self.get("schools:grade_level_edit", pk=grade_level.id)

        self.response_404(response)


class TestCourseDown(TestCase):
    def test_unauthenticated_access(self):
        grade_level = GradeLevelFactory()
        course = CourseFactory(grade_levels=[grade_level])
        self.assertLoginRequired(
            "schools:course_down", pk=grade_level.id, course_id=course.id
        )

    def test_post(self):
        """A course is moved down."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        first_course = CourseFactory(grade_levels=[grade_level])
        second_course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            response = self.post(
                "schools:course_down", pk=grade_level.id, course_id=first_course.id
            )

        assert response.get("Location") == self.reverse(
            "schools:grade_level_edit", grade_level.id
        )
        assert list(grade_level.get_ordered_courses()) == [second_course, first_course]

    def test_next_url(self):
        """The view redirects to the next URL when present."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        first_course = CourseFactory(grade_levels=[grade_level])
        CourseFactory(grade_levels=[grade_level])
        url = self.reverse(
            "schools:course_down", pk=grade_level.id, course_id=first_course.id
        )
        next_url = self.reverse("core:terms")
        url += f"?next={next_url}"

        with self.login(user):
            response = self.post(url)

        assert response.get("Location") == next_url


class TestCourseUp(TestCase):
    def test_unauthenticated_access(self):
        grade_level = GradeLevelFactory()
        course = CourseFactory(grade_levels=[grade_level])
        self.assertLoginRequired(
            "schools:course_up", pk=grade_level.id, course_id=course.id
        )

    def test_post(self):
        """A course is moved up."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        first_course = CourseFactory(grade_levels=[grade_level])
        second_course = CourseFactory(grade_levels=[grade_level])

        with self.login(user):
            response = self.post(
                "schools:course_up", pk=grade_level.id, course_id=second_course.id
            )

        assert response.get("Location") == self.reverse(
            "schools:grade_level_edit", grade_level.id
        )
        assert list(grade_level.get_ordered_courses()) == [second_course, first_course]

    def test_next_url(self):
        """The view redirects to the next URL when present."""
        user = self.make_user()
        grade_level = GradeLevelFactory(school_year__school=user.school)
        CourseFactory(grade_levels=[grade_level])
        second_course = CourseFactory(grade_levels=[grade_level])
        url = self.reverse(
            "schools:course_up", pk=grade_level.id, course_id=second_course.id
        )
        next_url = self.reverse("core:terms")
        url += f"?next={next_url}"

        with self.login(user):
            response = self.post(url)

        assert response.get("Location") == next_url


class TestSchoolBreakCreateView(TestCase):
    def test_unauthenticated_access(self):
        school_year = SchoolYearFactory()
        self.assertLoginRequired("schools:school_break_create", pk=school_year.id)

    def test_get(self):
        user = self.make_user()
        school_year = SchoolYearFactory(school=user.school)
        enrollment = EnrollmentFactory(grade_level__school_year=school_year)

        with self.login(user):
            self.get_check_200("schools:school_break_create", pk=school_year.id)

        assert self.get_context("school_year") == school_year
        assert self.get_context("create")
        assert self.get_context("students") == [enrollment.student]

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
                "schools:school_break_create", pk=school_year.id, data=data
            )

        school_break = SchoolBreak.objects.get(school_year=school_year)
        assert school_break.description == "Christmas"
        assert school_break.start_date == school_year.start_date
        assert school_break.end_date == school_year.start_date
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", pk=school_year.id
        )

    def test_not_found_for_other_school(self):
        """A user cannot add a school break to another user's school year."""
        user = self.make_user()
        school_year = SchoolYearFactory()

        with self.login(user):
            response = self.get("schools:school_break_create", pk=school_year.id)

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
                "schools:school_break_create", pk=school_year.id, data=data
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
                "schools:school_break_create", pk=school_year.id, data=data
            )

        form = self.get_context("form")
        assert form.non_field_errors() == [
            "A school break cannot be created for a different user's school year."
        ]
        self.response_200(response)


class TestSchoolBreakUpdateView(TestCase):
    def test_unauthenticated_access(self):
        school_break = SchoolBreakFactory()
        self.assertLoginRequired("schools:school_break_edit", pk=school_break.id)

    def test_get(self):
        user = self.make_user()
        school_break = SchoolBreakFactory(school_year__school=user.school)
        # Make only one student on break.
        enrollment_1 = EnrollmentFactory(
            student__first_name="Alice",
            grade_level__school_year=school_break.school_year,
        )
        school_break.students.add(enrollment_1.student)
        enrollment_2 = EnrollmentFactory(
            student__first_name="Bob", grade_level=enrollment_1.grade_level
        )

        with self.login(user):
            self.get_check_200("schools:school_break_edit", pk=school_break.id)

        assert self.get_context("school_year") == school_break.school_year
        students = self.get_context("students")
        assert students == [enrollment_1.student, enrollment_2.student]
        assert students[0].is_on_break
        assert not students[1].is_on_break

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
                "schools:school_break_edit", pk=school_break.id, data=data
            )

        school_break.refresh_from_db()
        assert school_break.description == "Christmas"
        assert school_break.start_date == school_break.school_year.start_date
        assert school_break.end_date == school_break.school_year.start_date
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", pk=school_break.school_year.id
        )

    def test_only_users_breaks(self):
        """A user can only edit their own school breaks."""
        user = self.make_user()
        school_break = SchoolBreakFactory()

        with self.login(user):
            response = self.get("schools:school_break_edit", pk=school_break.id)

        self.response_404(response)


class TestSchoolBreakDeleteView(TestCase):
    def test_unauthenticated_access(self):
        school_break = SchoolBreakFactory()
        self.assertLoginRequired("schools:school_break_delete", pk=school_break.id)

    def test_post(self):
        user = self.make_user()
        school_break = SchoolBreakFactory(school_year__school=user.school)

        with self.login(user):
            response = self.post("schools:school_break_delete", pk=school_break.id)

        assert SchoolBreak.objects.count() == 0
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "schools:school_year_detail", pk=school_break.school_year.id
        )

    def test_post_other_user(self):
        """A user may not delete another user's break."""
        user = self.make_user()
        school_break = SchoolBreakFactory()

        with self.login(user):
            response = self.post("schools:school_break_delete", pk=school_break.id)

        self.response_404(response)
