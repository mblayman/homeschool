import datetime
from unittest import mock

import pytz
from dateutil.relativedelta import MO, SU, relativedelta

from homeschool.students.tests.factories import StudentFactory
from homeschool.test import TestCase


class TestIndex(TestCase):
    def test_ok(self):
        self.get_check_200("core:index")


class TestApp(TestCase):
    def test_ok(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("core:app")

    def test_unauthenticated_access(self):
        self.assertLoginRequired("core:app")

    @mock.patch("homeschool.core.views.timezone")
    def test_has_monday(self, timezone):
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        monday = now.date() + relativedelta(weekday=MO(-1))
        timezone.now.return_value = now

        with self.login(user):
            self.get("core:app")

        self.assertContext("monday", monday)

    @mock.patch("homeschool.core.views.timezone")
    def test_has_sunday(self, timezone):
        user = self.make_user()
        now = datetime.datetime(2020, 1, 26, tzinfo=pytz.utc)
        sunday = now.date() + relativedelta(weekday=SU(+1))
        timezone.now.return_value = now

        with self.login(user):
            self.get("core:app")

        self.assertContext("sunday", sunday)

    def test_has_students(self):
        user = self.make_user()
        student = StudentFactory(school=user.school)

        with self.login(user), self.assertNumQueries(5):
            self.get("core:app")

        self.assertContext("students", [student])
