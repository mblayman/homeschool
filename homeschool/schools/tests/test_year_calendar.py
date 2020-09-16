import datetime

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from homeschool.schools.models import SchoolBreak
from homeschool.schools.tests.factories import SchoolBreakFactory, SchoolYearFactory
from homeschool.schools.year_calendar import YearCalendar
from homeschool.test import TestCase


class TestYearCalendar(TestCase):
    def test_builds_for_school_year(self):
        """A calendar of the school year is created."""
        today = timezone.localdate()
        school_year = SchoolYearFactory(
            start_date=today + relativedelta(day=1),
            end_date=today + relativedelta(months=1, day=1),
        )
        year_calendar = YearCalendar(school_year, school_year.start_date)

        calendar = year_calendar.build()

        assert len(calendar["months"]) == 2

    def test_only_look_ahead_months(self):
        """In the current school year, show only the look ahead months by default."""
        today = timezone.localdate()
        school_year = SchoolYearFactory(
            start_date=today + relativedelta(day=1),
            end_date=today + relativedelta(months=12, day=1),
        )
        year_calendar = YearCalendar(school_year, school_year.start_date)

        calendar = year_calendar.build()

        assert len(calendar["months"]) == YearCalendar.months_to_look_ahead

    def test_no_show_beyond_school_year(self):
        """At the end of the current year, do not show month beyond the school year."""
        today = timezone.localdate()
        school_year = SchoolYearFactory(
            start_date=today + relativedelta(day=1),
            end_date=today + relativedelta(months=12, day=1),
        )
        year_calendar = YearCalendar(
            school_year, school_year.start_date + relativedelta(months=10, day=1)
        )

        calendar = year_calendar.build()

        assert len(calendar["months"]) == 3

    def test_all_months(self):
        """All months are shown when the option is set."""
        today = timezone.localdate()
        school_year = SchoolYearFactory(
            start_date=today + relativedelta(day=1),
            end_date=today + relativedelta(months=12, day=1),
        )
        year_calendar = YearCalendar(school_year, school_year.start_date)

        calendar = year_calendar.build(show_all=True)

        assert len(calendar["months"]) == 13

    def test_calendar_with_break_types(self):
        """The calendar supports single day breaks and multi-day breaks."""
        # Freeze the time because the month dates may not be deterministic
        # for fitting the dates to check into a week.
        today = datetime.date(2020, 7, 18)
        school_year = SchoolYearFactory(
            start_date=today + relativedelta(day=1),
            end_date=today + relativedelta(months=1, day=1),
        )
        SchoolBreakFactory(
            school_year=school_year,
            start_date=school_year.start_date,
            end_date=school_year.start_date,
        )
        SchoolBreakFactory(
            school_year=school_year,
            start_date=school_year.start_date + datetime.timedelta(days=1),
            end_date=school_year.start_date + datetime.timedelta(days=3),
        )
        year_calendar = YearCalendar(school_year, school_year.start_date)

        calendar = year_calendar.build()

        dates = calendar["months"][0]["weeks"][0]
        # There can be padding in the month so the test must search for the first day.
        first_date_data = {}
        first_day_index = 0
        for index, date_data in enumerate(dates):
            if date_data["day"] == 1:
                first_date_data = date_data
                first_day_index = index
                break
        assert first_date_data["school_break"] is not None
        assert first_date_data["date_type"] == SchoolBreak.DateType.SINGLE
        start_date_data = dates[first_day_index + 1]
        assert start_date_data["school_break"] is not None
        assert start_date_data["date_type"] == SchoolBreak.DateType.START
        middle_date_data = dates[first_day_index + 2]
        assert middle_date_data["school_break"] is not None
        assert middle_date_data["date_type"] == SchoolBreak.DateType.MIDDLE
        end_date_data = dates[first_day_index + 3]
        assert end_date_data["school_break"] is not None
        assert end_date_data["date_type"] == SchoolBreak.DateType.END
