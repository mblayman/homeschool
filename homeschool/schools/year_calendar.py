import calendar
import datetime

from dateutil.relativedelta import relativedelta


class YearCalendar:
    """A calendar of information related to a school year."""

    def __init__(self, school_year, today):
        self.school_year = school_year
        self.today = today
        self.calendar = calendar.Calendar()
        self.is_current_school_year = (
            self.school_year.start_date <= self.today <= self.school_year.end_date
        )

    def build(self):
        """Build a calendar structure that can be rendered."""
        # TODO: Test this.
        # Use the 1st so any school year ending on a 1st of the month isn't skipped.
        current_date = self.school_year.start_date + relativedelta(day=1)

        months: list = []
        while current_date <= self.school_year.end_date:
            months.append(self._build_month(current_date.year, current_date.month))
            current_date = current_date + relativedelta(months=1)

        return {"months": months, "header_labels": self._build_header_labels(months)}

    def _build_month(self, year, month):
        """Initialize the month with any dates it should skip."""
        dates: list = []
        done_with_blanks = False
        for day in self.calendar.itermonthdays(year, month):
            if day == 0:
                # Skip any trailing dates in the next month.
                if done_with_blanks:
                    break
                dates.append({"day": ""})
            else:
                done_with_blanks = True
                dates.append(self._build_date(datetime.date(year, month, day)))
        return {"name": calendar.month_name[month], "dates": dates}

    def _build_date(self, current_date):
        """Build a date dictionary with all the data to render."""
        return {
            "date": current_date,
            "day": current_date.day,
            "in_school_year": self.school_year.start_date
            <= current_date
            <= self.school_year.end_date,
            "is_school_day": self.school_year.runs_on(current_date),
            "is_today": current_date == self.today,
            "show_as_past": self.is_current_school_year and current_date < self.today,
        }

    def _build_header_labels(self, months):
        """Build the list of display labels for the header."""
        labels = ["M", "T", "W", "T", "F", "S", "S"]
        max_month_dates = max(len(month["dates"]) for month in months)
        header_labels = labels * ((max_month_dates // 7) + 1)
        return header_labels[:max_month_dates]
