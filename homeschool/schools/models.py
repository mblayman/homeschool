import datetime
from typing import Optional

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import cached_property
from hashid_field import HashidAutoField

from homeschool.core.models import DaysOfWeekModel
from homeschool.students.models import Student
from homeschool.users.models import User


class School(models.Model):
    """A school to hold students"""

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="The school administrator",
    )

    def __str__(self):
        return f"School ({self.admin.email})"


@receiver(post_save, sender=User)
def create_school(sender, instance, created, **kwargs):
    """A new user gets an associated school."""
    if created:
        School.objects.create(admin=instance)


class SchoolYear(DaysOfWeekModel):
    """A school year to bound start and end dates of the academic year"""

    id = HashidAutoField(
        primary_key=True, salt=f"schoolyear{settings.HASHID_FIELD_SALT}"
    )
    school = models.ForeignKey("schools.School", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

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

    def contains(self, day: datetime.date) -> bool:
        """Check if the day is in the school year."""
        return self.start_date <= day <= self.end_date

    def is_break(
        self, break_date: datetime.date, *, student: Optional[Student]
    ) -> bool:
        """Check if the break date is a school break."""
        return self.get_break(break_date, student=student) is not None

    def get_break(
        self, break_date: datetime.date, *, student: Optional[Student]
    ) -> Optional["SchoolBreak"]:
        """Get a school break if the date is contained in the break."""
        # TODO 434: use the student parameter
        return self._school_breaks_by_date.get(break_date)

    @cached_property
    def _school_breaks_by_date(self) -> dict[datetime.date, "SchoolBreak"]:
        """Get the school breaks grouped by the dates."""
        breaks_by_date = {}
        for school_break in self.breaks.all():
            current_date = school_break.start_date
            while current_date <= school_break.end_date:
                breaks_by_date[current_date] = school_break
                current_date = current_date + datetime.timedelta(days=1)
        return breaks_by_date

    def get_task_count_in_range(self, course, start_date, end_date, student):
        """Get the task count for a course and factor in any breaks.

        Be inclusive of start and end.
        """
        if start_date > end_date:
            return 1 if course.runs_on(start_date) else 0

        task_count = 0
        date_to_check = start_date
        while date_to_check <= end_date:
            if not self.is_break(date_to_check, student=student) and course.runs_on(
                date_to_check
            ):
                task_count += 1
            date_to_check += datetime.timedelta(days=1)

        return task_count

    def get_next_course_day(self, course, day, student):
        """Get the next course day after the provided day (considering breaks)."""
        next_course_day = course.get_next_day_from(day)
        # When the course isn't meeting the next day is the same. Bail early.
        if next_course_day == day:
            return day

        while next_course_day < self.end_date:
            if not self.is_break(next_course_day, student=student):
                return next_course_day
            next_course_day = course.get_next_day_from(next_course_day)

        return next_course_day

    def __str__(self):
        if self.start_date.year == self.end_date.year:
            return str(self.start_date.year)
        return f"{self.start_date.year}–{self.end_date.year}"


class GradeLevel(models.Model):
    """A student is in a grade level in a given school year"""

    id = HashidAutoField(
        primary_key=True, salt=f"gradelevel{settings.HASHID_FIELD_SALT}"
    )
    name = models.CharField(max_length=128)
    school_year = models.ForeignKey(
        "schools.SchoolYear", on_delete=models.CASCADE, related_name="grade_levels"
    )

    def get_ordered_courses(self):
        """Get the courses in their proper order.

        Since ordering is defined on the through model, this is a reasonable
        way to get the courses.
        """
        from homeschool.courses.models import GradeLevelCoursesThroughModel

        courses = [
            gc.course
            for gc in GradeLevelCoursesThroughModel.objects.filter(
                grade_level=self
            ).select_related("course")
        ]
        # Eager load the school year to avoid performance hit
        # of hitting the cached property on course in a loop.
        school_year = self.school_year
        for course in courses:
            course.school_year = school_year
        return courses

    def get_active_courses(self):
        """Get the courses that are active."""
        return [course for course in self.get_ordered_courses() if course.is_active]

    def __str__(self):
        return self.name


class SchoolBreak(models.Model):
    """A break day in the schedule."""

    id = HashidAutoField(
        primary_key=True, salt=f"schoolbreak{settings.HASHID_FIELD_SALT}"
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    description = models.TextField(blank=True)
    school_year = models.ForeignKey(
        "schools.SchoolYear", on_delete=models.CASCADE, related_name="breaks"
    )

    class DateType(models.IntegerChoices):
        SINGLE = 1
        START = 2
        END = 3
        MIDDLE = 4
        NOT_A_BREAK = 5

    class Meta:
        ordering = ["start_date"]

    def __str__(self):
        return f"School Break {self.start_date}"

    def get_date_type(self, break_date):
        """Get what type a break date is."""
        if break_date < self.start_date or break_date > self.end_date:
            return self.DateType.NOT_A_BREAK
        if self.start_date == self.end_date:
            return self.DateType.SINGLE
        if break_date == self.start_date:
            return self.DateType.START
        if break_date == self.end_date:
            return self.DateType.END
        return self.DateType.MIDDLE
