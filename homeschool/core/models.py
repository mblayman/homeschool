import datetime

from django.db import models
from waffle.models import AbstractUserFlag


class Flag(AbstractUserFlag):
    """Customizable version of Waffle's Flag model."""


class DaysOfWeekModel(models.Model):
    """A model that includes the days of the week"""

    class Meta:
        abstract = True

    # Instead of bringing in django-bitfield, do this directly
    # since the use case is constrained to seven values.
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 4
    THURSDAY = 8
    FRIDAY = 16
    SATURDAY = 32
    SUNDAY = 64
    WEEK = (MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY)

    days_of_week = models.PositiveIntegerField(
        help_text="The days of the week when this runs",
        default=MONDAY + TUESDAY + WEDNESDAY + THURSDAY + FRIDAY,
    )

    # Lookup table to convert a date into the model representation of day.
    date_to_day = {
        1: MONDAY,
        2: TUESDAY,
        3: WEDNESDAY,
        4: THURSDAY,
        5: FRIDAY,
        6: SATURDAY,
        7: SUNDAY,
    }

    def get_week_dates_for(self, week):
        """Get the list of week dates that the record runs on for the given week.

        Week is a range tuple in the form of (monday, sunday).
        """
        week_date = week[0]
        week_dates = []
        for day in self.WEEK:
            if self.runs_on(day):
                week_dates.append(week_date)
            week_date += datetime.timedelta(days=1)
        return week_dates

    def runs_on(self, day):
        """Check if a school year runs on the given day.

        Days of week is a bit field and day acts as a bitmask.
        """
        if isinstance(day, datetime.date):
            day = self.date_to_day[day.isoweekday()]
        return bool(self.days_of_week & day)
