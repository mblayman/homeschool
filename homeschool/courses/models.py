import uuid

from django.db import models
from ordered_model.models import OrderedModel, OrderedModelManager

from homeschool.core.models import DaysOfWeekModel


class Course(DaysOfWeekModel):
    """A course is a container for tasks in a certain subject area."""

    name = models.CharField(max_length=256)
    grade_level = models.ForeignKey(
        "schools.GradeLevel", on_delete=models.CASCADE, related_name="courses"
    )
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)

    def __str__(self):
        return self.name


class GradedWork(models.Model):
    """Any type of work that a student might be graded on like a test or quiz."""


class CourseTaskManager(OrderedModelManager):
    pass


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
    graded_work = models.ForeignKey(
        "courses.GradedWork", null=True, blank=True, on_delete=models.SET_NULL
    )

    objects = CourseTaskManager()
    order_with_respect_to = "course"

    def __str__(self):
        return self.description
