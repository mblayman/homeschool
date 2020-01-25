import uuid

from django.db import models


class Course(models.Model):
    """A course is a container for tasks in a certain subject area."""

    name = models.CharField(max_length=256)
    grade_level = models.ForeignKey("schools.GradeLevel", on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class CourseTask(models.Model):
    """A student's required action in a course."""

    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)
    description = models.TextField()
    duration = models.PositiveIntegerField(
        help_text="The expected length of the task in minutes"
    )

    def __str__(self):
        return self.description
