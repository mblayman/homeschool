from django.conf import settings
from django.db import models


class School(models.Model):
    """A school to hold students"""

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="The school administrator",
    )


class SchoolYear(models.Model):
    """A school year to bound start and end dates of the academic year"""

    # Instead of bringing in django-bitfield, do this directly
    # since the use case is constrained to seven values.
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 4
    THURSDAY = 8
    FRIDAY = 16
    SATURDAY = 32
    SUNDAY = 64

    school = models.ForeignKey("schools.School", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    days_of_week = models.PositiveIntegerField(
        help_text="The days of the week when school is in session",
        default=MONDAY + TUESDAY + WEDNESDAY + THURSDAY + FRIDAY,
    )

    def runs_on(self, day):
        """Check if a school year runs on the given day.

        Days of week is a bit field and day acts as a bitmask.
        """
        return bool(self.days_of_week & day)


class GradeLevel(models.Model):
    """A student is in a grade level in a given school year"""

    name = models.CharField(max_length=128)
    school_year = models.ForeignKey("schools.SchoolYear", on_delete=models.CASCADE)

    def __str__(self):
        return self.name
