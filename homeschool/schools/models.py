from django.conf import settings
from django.db import models

from homeschool.core.models import DaysOfWeekModel


class School(models.Model):
    """A school to hold students"""

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="The school administrator",
    )


class SchoolYear(DaysOfWeekModel):
    """A school year to bound start and end dates of the academic year"""

    school = models.ForeignKey("schools.School", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()


class GradeLevel(models.Model):
    """A student is in a grade level in a given school year"""

    name = models.CharField(max_length=128)
    school_year = models.ForeignKey("schools.SchoolYear", on_delete=models.CASCADE)

    def __str__(self):
        return self.name
