import uuid
from typing import Optional

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from homeschool.core.models import DaysOfWeekModel
from homeschool.users.models import User


class School(models.Model):
    """A school to hold students"""

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="The school administrator",
    )


@receiver(post_save, sender=User)
def create_school(sender, instance, created, **kwargs):
    """A new user gets an associated school."""
    if created:
        School.objects.create(admin=instance)


class SchoolYear(DaysOfWeekModel):
    """A school year to bound start and end dates of the academic year"""

    school = models.ForeignKey("schools.School", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)

    @classmethod
    def get_current_year_for(cls, user: User) -> Optional["SchoolYear"]:
        """Get a current school year for the user.

        Pick the current school if it's available.
        If not, look ahead to the future so a user can plan
        appropriately for the new school year.
        """
        today = user.get_local_today()
        school_year = SchoolYear.objects.filter(
            school__admin=user, start_date__lte=today, end_date__gte=today
        ).first()

        # Look for a future school year if there is no current one.
        # This is for new users who may be building their school year
        # for the first time.
        if not school_year:
            school_year = SchoolYear.objects.filter(
                school__admin=user, start_date__gt=today
            ).first()

        return school_year

    def __str__(self):
        if self.start_date.year == self.end_date.year:
            return str(self.start_date.year)
        return f"{self.start_date.year}–{self.end_date.year}"


class GradeLevel(models.Model):
    """A student is in a grade level in a given school year"""

    name = models.CharField(max_length=128)
    school_year = models.ForeignKey(
        "schools.SchoolYear", on_delete=models.CASCADE, related_name="grade_levels"
    )
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)

    def __str__(self):
        return self.name
