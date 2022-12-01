import datetime

from homeschool.core.schedules import Week
from homeschool.schools.tests.factories import GradeLevelFactory, SchoolYearFactory
from homeschool.students.tests.factories import EnrollmentFactory
from homeschool.teachers.tests.factories import ChecklistFactory
from homeschool.test import TestCase


class TestChecklist(TestCase):
    def test_ok(self):
        user = self.make_user()
        week = Week(datetime.date(2022, 6, 15))
        SchoolYearFactory(
            school__admin=user, start_date=week.first_day, end_date=week.last_day
        )

        with self.login(user):
            self.get_check_200("teachers:checklist", 2022, 6, 15)

        self.assertInContext("schedules")
        assert self.get_context("week") == week

    def test_school_start_midweek(self):
        """A school year that starts midweek will still show a checklist."""
        user = self.make_user()
        week = Week(datetime.date(2022, 11, 27))
        school_year = SchoolYearFactory(
            school__admin=user,
            start_date=week.first_day + datetime.timedelta(days=1),
            end_date=week.last_day,
        )
        grade_level = GradeLevelFactory(school_year=school_year)
        EnrollmentFactory(grade_level=grade_level, student__school=user.school)

        with self.login(user):
            self.get_check_200("teachers:checklist", 2022, 11, 27)

        assert self.get_context("schedules")
        assert self.get_context("week") == week


class TestEditChecklist(TestCase):
    def test_authorization(self):
        """A user must be the admin of the school."""
        user = self.make_user()
        week = Week(datetime.date(2022, 6, 15))
        SchoolYearFactory(start_date=week.first_day, end_date=week.last_day)

        with self.login(user):
            response = self.get("teachers:edit_checklist", 2022, 6, 15)

        assert response.status_code == 404

    def test_get(self):
        """The edit form is displayed."""
        user = self.make_user()
        week = Week(datetime.date(2022, 6, 15))
        school_year = SchoolYearFactory(
            school__admin=user, start_date=week.first_day, end_date=week.last_day
        )
        checklist = ChecklistFactory(school_year=school_year)

        with self.login(user):
            self.get_check_200("teachers:edit_checklist", 2022, 6, 15)

        assert self.get_context("checklist") == checklist
        self.assertInContext("schedules")
        assert self.get_context("week") == week

    def test_post(self):
        """The user returns to the checklist view."""
        user = self.make_user()
        week = Week(datetime.date(2022, 6, 15))
        SchoolYearFactory(
            school__admin=user, start_date=week.first_day, end_date=week.last_day
        )

        with self.login(user):
            response = self.post("teachers:edit_checklist", 2022, 6, 15, data={})

        assert response.status_code == 302
        assert response["Location"] == self.reverse("teachers:checklist", 2022, 6, 15)
