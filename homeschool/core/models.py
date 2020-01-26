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

    days_of_week = models.PositiveIntegerField(
        help_text="The days of the week when school is in session",
        default=MONDAY + TUESDAY + WEDNESDAY + THURSDAY + FRIDAY,
    )

    def runs_on(self, day):
        """Check if a school year runs on the given day.

        Days of week is a bit field and day acts as a bitmask.
        """
        return bool(self.days_of_week & day)

    @property
    def total_week_days(self):
        """Get the total number of selected days of the week."""
        total = 0
        for shift_bits in range(7):
            total += (self.days_of_week >> shift_bits) % 2
        return total
