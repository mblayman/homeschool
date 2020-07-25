import datetime
import uuid

from django.db import models
from ordered_model.models import OrderedModel

from homeschool.core.compatibility import OrderedModelQuerySet
from homeschool.core.models import DaysOfWeekModel


class Course(DaysOfWeekModel):
    """A course is a container for tasks in a certain subject area."""

    name = models.CharField(max_length=256)
    grade_levels = models.ManyToManyField(
        "schools.GradeLevel",
        related_name="courses",
        through="courses.GradeLevelCoursesThroughModel",
    )
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)
    default_task_duration = models.IntegerField(
        default=30, help_text="The default task duration in minutes"
    )

    @property
    def is_running(self):
        """Check if the course is running on any days of the week."""
        return self.days_of_week != self.NO_DAYS

    @property
    def has_many_grade_levels(self):
        """Check if multiple grade levels are associated with the course."""
        return self.grade_levels.count() > 1

    def get_task_count_in_range(self, start_date, end_date):
        """Get the number of tasks for the date range.

        Be inclusive of start and end.
        """
        if start_date > end_date:
            return 1 if self.runs_on(start_date) else 0

        task_count = 0
        date_to_check = start_date
        while date_to_check <= end_date:
            if self.runs_on(date_to_check):
                task_count += 1
            date_to_check += datetime.timedelta(days=1)

        return task_count

    def __str__(self):
        return self.name


class GradeLevelCoursesThroughModel(OrderedModel):
    grade_level = models.ForeignKey("schools.GradeLevel", on_delete=models.CASCADE)
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE)
    order_with_respect_to = "grade_level"

    objects = models.Manager.from_queryset(OrderedModelQuerySet)()

    class Meta:
        ordering = ("grade_level", "order")


class CourseTask(OrderedModel):
    """A student's required action in a course."""

    class Meta(OrderedModel.Meta):
        pass

    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="course_tasks"
    )
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)
    description = models.TextField()
    duration = models.PositiveIntegerField(
        help_text="The expected length of the task in minutes"
    )
    grade_level = models.ForeignKey(
        "schools.GradeLevel",
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
        help_text="A grade level when a task is specific to a grade",
    )

    order_with_respect_to = "course"

    def __str__(self):
        return self.description


class GradedWork(models.Model):
    """Any type of work that a student might be graded on like a test or quiz."""

    course_task = models.OneToOneField(
        "courses.CourseTask", on_delete=models.CASCADE, related_name="graded_work"
    )
