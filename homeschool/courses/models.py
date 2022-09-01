from __future__ import annotations

from typing import Optional

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from hashid_field import HashidAutoField
from ordered_model.models import OrderedModel, OrderedModelQuerySet

from homeschool.core.models import DaysOfWeekModel
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.users.models import User

from .exceptions import NoSchoolYearError


class Course(DaysOfWeekModel):
    """A course is a container for tasks in a certain subject area."""

    id = HashidAutoField(primary_key=True, salt=f"course{settings.HASHID_FIELD_SALT}")
    name = models.CharField(max_length=256)
    grade_levels = models.ManyToManyField(
        "schools.GradeLevel",
        related_name="courses",
        through="courses.GradeLevelCoursesThroughModel",
    )
    default_task_duration = models.IntegerField(
        default=30, help_text="The default task duration in minutes"
    )
    is_active = models.BooleanField(
        default=True, help_text="Is this course active in the schedule?"
    )

    @classmethod
    def from_school_year(cls, school_year: SchoolYear) -> models.QuerySet[Course]:
        grade_levels = GradeLevel.objects.filter(school_year=school_year)
        return cls.objects.filter(grade_levels__in=grade_levels).distinct()

    @property
    def is_running(self):
        """Check if the course is running on any days of the week."""
        return self.days_of_week != self.NO_DAYS

    @cached_property
    def has_many_grade_levels(self):
        """Check if multiple grade levels are associated with the course."""
        return self.grade_levels.count() > 1

    @cached_property
    def school_year(self):
        """Get the school year for the course."""
        grade_level = self.grade_levels.select_related("school_year").first()
        if grade_level:
            return grade_level.school_year
        raise NoSchoolYearError("The course has no school year.")

    def belongs_to(self, user):
        """Check if the course belongs to the user."""
        grade_levels = GradeLevel.objects.filter(
            school_year__school__admin=user
        ).values_list("id", flat=True)
        return Course.objects.filter(id=self.id, grade_levels__in=grade_levels).exists()

    def copy_to(self, new_course):
        """Copy the course and its associated items to the new course."""
        tasks_to_copy = self.course_tasks.all().prefetch_related("graded_work")
        new_tasks = [
            CourseTask(
                course=new_course, description=task.description, duration=task.duration
            )
            for task in tasks_to_copy
        ]
        CourseTask.objects.bulk_create(new_tasks)

        # To avoid creating tasks individually, a second pass is needed
        # to add any graded work.
        tasks_to_compare = zip(
            tasks_to_copy, CourseTask.objects.filter(course=new_course)
        )
        graded_work = [
            GradedWork(course_task=copied_task)
            for task_to_copy, copied_task in tasks_to_compare
            if hasattr(task_to_copy, "graded_work")
        ]
        GradedWork.objects.bulk_create(graded_work)

        resources_to_copy = [
            CourseResource(
                course=new_course, title=resource.title, details=resource.details
            )
            for resource in self.resources.all()
        ]
        CourseResource.objects.bulk_create(resources_to_copy)

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

    id = HashidAutoField(
        primary_key=True, salt=f"coursetask{settings.HASHID_FIELD_SALT}"
    )
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="course_tasks"
    )
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

    @classmethod
    def get_by_id(cls, user: User, id_str: str) -> Optional[CourseTask]:
        """Get a task for a user by an id."""
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return CourseTask.objects.filter(
            course__grade_levels__in=grade_levels, id=id_str
        ).first()

    @property
    def is_graded(self):
        """Check if the task is graded.

        Reminder: This triggers a db query since it's a related_name access.
        The foreign key is on the GradedWork model so the db access can't be avoided
        from the task side.
        """
        return hasattr(self, "graded_work")

    def __str__(self):
        return self.description


class GradedWork(models.Model):
    """Any type of work that a student might be graded on like a test or quiz."""

    course_task = models.OneToOneField(
        "courses.CourseTask", on_delete=models.CASCADE, related_name="graded_work"
    )


class CourseResource(models.Model):
    """A resource related to a course (e.g., a book or workbook)"""

    id = HashidAutoField(
        primary_key=True, salt=f"courseresource{settings.HASHID_FIELD_SALT}"
    )
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="resources"
    )
    title = models.CharField(max_length=512)
    details = models.TextField(blank=True)

    def __str__(self):
        return self.title
