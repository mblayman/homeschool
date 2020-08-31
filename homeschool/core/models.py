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
    NO_DAYS = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 4
    THURSDAY = 8
    FRIDAY = 16
    SATURDAY = 32
    SUNDAY = 64
    WEEK = (SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY)
    ALL_DAYS = sum(WEEK)

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

    # Lookup table to get displayable name.
    day_to_display_day = {
        SUNDAY: "Sunday",
        MONDAY: "Monday",
        TUESDAY: "Tuesday",
        WEDNESDAY: "Wednesday",
        THURSDAY: "Thursday",
        FRIDAY: "Friday",
        SATURDAY: "Saturday",
    }

    # Lookup table to get abbreviated displayable name.
    day_to_display_day_abbreviation = {
        SUNDAY: "Su",
        MONDAY: "M",
        TUESDAY: "T",
        WEDNESDAY: "W",
        THURSDAY: "R",
        FRIDAY: "F",
        SATURDAY: "Sa",
    }

    @property
    def display_days(self):
        """Display the week days this model runs on."""
        display_days = [self.day_to_display_day[day] for day in self._running_days]
        day_count = len(display_days)
        # More than 2 days - Monday, Tuesday, and Wednesday
        if day_count > 2:
            display_days[-1] = "and {}".format(display_days[-1])
            return ", ".join(display_days)
        # 2 days - Monday and Tuesday
        elif day_count == 2:
            return " and ".join(display_days)
        # 1 day - Monday
        elif day_count == 1:
            return display_days[0]
        # 0 days - show nothing
        else:
            return ""

    @property
    def display_abbreviated_days(self):
        """Display the abbreviated week days this model runs on."""
        abbreviated_days = "".join(
            [self.day_to_display_day_abbreviation[day] for day in self._running_days]
        )
        return abbreviated_days if abbreviated_days else "Not Running"

    @property
    def _running_days(self):
        """Get all the days that this model runs on."""
        return [day for day in self.WEEK if self.runs_on(day)]

    def get_week_dates_for(self, week):
        """Get the list of week dates that the record runs on for the given week. """
        week_date = week.first_day
        week_dates = []
        for day in self.WEEK:
            if self.runs_on(day):
                week_dates.append(week_date)
            week_date += datetime.timedelta(days=1)
        return week_dates

    def last_school_day_for(self, week):
        """Get that last school day that this model runs.

        If the model isn't running any week days, fall back to the first day.
        """
        week_date = week.last_day
        for day in reversed(self.WEEK):
            if self.runs_on(week_date):
                return week_date
            week_date -= datetime.timedelta(days=1)
        return week.first_day

    def runs_on(self, day):
        """Check if the model runs on the given day.

        Days of week is a bit field and day acts as a bitmask.
        """
        if isinstance(day, datetime.date):
            day = self.date_to_day[day.isoweekday()]
        return bool(self.days_of_week & day)

    def get_previous_day_from(self, day: datetime.date) -> datetime.date:
        """Get the previous day that runs relative to the provided date.

        Return the same date if the record runs on no days.
        """
        # Guard against an infinite loop.
        # A record with no running days will never terminate.
        if not self.days_of_week:
            return day

        previous_day = day - datetime.timedelta(days=1)
        while not self.runs_on(previous_day):
            previous_day -= datetime.timedelta(days=1)
        return previous_day

    def get_next_day_from(self, day: datetime.date) -> datetime.date:
        """Get the next day that runs relative to the provided date.

        Return the same date if the record runs on no days.
        """
        # Guard against an infinite loop.
        # A record with no running days will never terminate.
        if not self.days_of_week:
            return day

        next_day = day + datetime.timedelta(days=1)
        while not self.runs_on(next_day):
            next_day += datetime.timedelta(days=1)
        return next_day
