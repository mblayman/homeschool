import datetime

from homeschool.core.schedules import Week
from homeschool.test import TestCase


class TestWeek(TestCase):
    def test_str(self):
        week = Week(datetime.date(2020, 8, 28))  # A Friday

        assert str(week) == "2020-08-23 - 2020-08-29"
