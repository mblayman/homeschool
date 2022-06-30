import datetime

from homeschool.core.schedules import Week
from homeschool.schools.tests.factories import SchoolYearFactory
from homeschool.test import TestCase


class TestChecklist(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("teachers:checklist", 2022, 6, 15)

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
