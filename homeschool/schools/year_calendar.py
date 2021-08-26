import calendar
import datetime

from dateutil.relativedelta import relativedelta

from .models import SchoolBreak


class YearCalendar:
    """A calendar of information related to a school year."""

    months_to_look_ahead = 4

    def __init__(self, school_year, today):
        self.school_year = school_year
        self.today = today
        self.calendar = calendar.Calendar(firstweekday=6)  # Start on Sunday.
        self.is_current_school_year = school_year.contains(today)

    def build(self, *, show_all=False):
        """Build a calendar structure that can be rendered."""
        # Use the 1st so any school year ending on a 1st of the month isn't skipped.
        if self.is_current_school_year and not show_all:
            current_date = self.today + relativedelta(day=1)
            months_to_build = self.months_to_look_ahead
        else:
            current_date = self.school_year.start_date + relativedelta(day=1)
            # Get the delta to be inclusive of the start and end months.
            delta = relativedelta(
                self.school_year.end_date + relativedelta(months=1, day=1),
                self.school_year.start_date + relativedelta(months=-1, day=31),
            )
            months_to_build = delta.years * 12 + delta.months

        months: list = []
        while months_to_build != 0 and current_date <= self.school_year.end_date:
            months.append(self._build_month(current_date.year, current_date.month))
            current_date = current_date + relativedelta(months=1)
            months_to_build -= 1

        return {"months": months}

    def _build_month(self, year, month):
        """Initialize the month with any dates it should skip."""
        weeks: list = []
        for week in self.calendar.monthdayscalendar(year, month):
            week_dates: list = []
            for day in week:
                if day == 0:
                    week_dates.append({"day": ""})
                else:
                    week_dates.append(self._build_date(datetime.date(year, month, day)))
            weeks.append(week_dates)
        return {"name": calendar.month_name[month], "weeks": weeks}

    def _build_date(self, current_date):
        """Build a date dictionary with all the data to render."""
        # TODO 434: pass in a student
        school_break = self.school_year.get_break(current_date, student=None)
        return {
            "date": current_date,
            "day": current_date.day,
            "in_school_year": self.school_year.start_date
            <= current_date
            <= self.school_year.end_date,
            "is_school_day": self.school_year.runs_on(current_date),
            "is_today": current_date == self.today,
            "show_as_past": self.is_current_school_year and current_date < self.today,
            "school_break": school_break,
            "date_type": school_break.get_date_type(current_date)
            if school_break
            else SchoolBreak.DateType.NOT_A_BREAK,
        }
