import datetime
from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.db import models
from django.db.models import Q
from hashid_field import HashidAutoField

from homeschool.core.schedules import Week

if TYPE_CHECKING:  # pragma: no cover
    from homeschool.courses.models import Course


class Student(models.Model):
    """The learner"""

    id = HashidAutoField(primary_key=True, salt=f"student{settings.HASHID_FIELD_SALT}")
    school = models.ForeignKey(
        "schools.School", on_delete=models.CASCADE, related_name="students"
    )
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Task lookup needs an enrollment and it's a common pattern
        # to get all the courses, then get the tasks for those courses.
        # By caching the enrollment when fetching all the courses,
        # a lot of queries to Enrollment are prevented.
        self._enrollment_by_course_cache = {}

    @classmethod
    def get_students_for(cls, school_year):
        """Get all the enrolled students for the school year."""
        enrollments = (
            Enrollment.objects.filter(grade_level__school_year=school_year)
            .order_by("grade_level")
            .select_related("student")
        )
        return [enrollment.student for enrollment in enrollments]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

    def get_week_schedule(self, school_year, today, week):
        """Get the student's week schedule for a given week.

        The schedule is calculated from the user's point of view in time
        as of today. The week is not necessarily *this* week.
        """
        week_dates = school_year.get_week_dates_for(week)
        week_end_date = school_year.last_school_day_for(week)
        week_coursework = self.get_week_coursework(week)

        courses = self.get_active_courses(school_year)
        completed_task_ids = list(
            Coursework.objects.filter(
                student=self, course_task__course__in=courses
            ).values_list("course_task_id", flat=True)
        )
        course_schedules = []
        for course in courses:
            if week_end_date > today and not course.is_running:
                continue

            course_schedule = {"course": course, "days": []}

            course_tasks = self._build_course_tasks(
                course,
                school_year,
                completed_task_ids,
                today,
                week.first_day,
                week_end_date,
                len(week_dates),
            )

            # Tasks should only appear *after* the last coursework date.
            last_coursework_date = self.get_last_coursework_date(
                week_coursework, course
            )

            for week_date in week_dates:
                school_break = school_year.get_break(week_date, student=self)
                course_schedule_item = {
                    "week_date": week_date,
                    "school_break": school_break,
                }
                course_schedule["days"].append(course_schedule_item)

                if school_break:
                    course_schedule_item["date_type"] = school_break.get_date_type(
                        week_date
                    )
                    continue

                # The first week of a school year should skip any days
                # before the year officially starts.
                if week_date < school_year.start_date:
                    continue

                if (
                    course.id in week_coursework
                    and week_date in week_coursework[course.id]
                ):
                    coursework_list = week_coursework[course.id][week_date]
                    course_schedule_item["coursework"] = coursework_list
                elif (
                    course.runs_on(week_date)
                    and course_tasks
                    and (
                        last_coursework_date is None or week_date > last_coursework_date
                    )
                    # Any tasks left for the week should only appear on or after today.
                    and week_date >= today
                ):
                    course_schedule_item["task"] = course_tasks.pop()
            course_schedules.append(course_schedule)
        return {"student": self, "courses": course_schedules}

    def _build_course_tasks(
        self,
        course,
        school_year,
        completed_task_ids,
        today,
        week_start_date,
        week_end_date,
        task_limit,
    ):
        """Build a list of course tasks that can be added to the schedule.

        The tasks are returned in reverse order so they can be popped
        like a stack for performance.
        """
        course_tasks: list = []
        # Only show tasks on current or future weeks.
        if week_end_date < today:
            return course_tasks

        task_index = self._get_course_task_index(
            course, today, week_start_date, school_year
        )

        # Doing this query in a loop is definitely an N+1 bug.
        # If it's possible to do a single query of all tasks
        # that groups by course then that would be better.
        # No need to over-optimize until that's a real issue.
        # I brought this up on the forum. It doesn't look like it's easy to fix.
        # https://forum.djangoproject.com/t/grouping-by-foreignkey-with-a-limit-per-group/979
        course_tasks = list(
            self.get_tasks_for(course).exclude(id__in=completed_task_ids)[
                task_index : task_index + task_limit
            ]
        )
        course_tasks.reverse()  # for the performance of pop below.
        return course_tasks

    def get_active_courses(self, school_year):
        """Get the active courses from the school year."""
        enrollment = (
            Enrollment.objects.filter(
                student=self, grade_level__in=school_year.grade_levels.all()
            )
            .select_related("grade_level")
            .first()
        )
        if enrollment:
            # This looks goofy, but it operates under the assumption
            # school year did all the prefetching on grade levels.
            for grade_level in school_year.grade_levels.all():
                if grade_level.id == enrollment.grade_level_id:
                    courses = grade_level.get_active_courses()
                    self._enrollment_by_course_cache.update(
                        {course: enrollment for course in courses}
                    )
                    return courses
        return []

    def get_week_coursework(self, week):
        """Get the coursework completed in the week.

        The data is in a dictionary for fast lookups.
        """
        week_coursework: dict = {}
        coursework_qs = (
            Coursework.objects.filter(
                student=self, completed_date__range=(week.first_day, week.last_day)
            )
            # Users can mark content as complete in whatever order they want,
            # but the display should match the task list.
            .order_by("course_task").select_related("course_task")
        )
        for coursework in coursework_qs:
            course_id = coursework.course_task.course_id
            if course_id not in week_coursework:
                week_coursework[course_id] = {}

            if coursework.completed_date not in week_coursework[course_id]:
                # It's possible for multiple coursework items to share the same
                # completion day because that's controlled by user input.
                week_coursework[course_id][coursework.completed_date] = []

            week_coursework[course_id][coursework.completed_date].append(coursework)

        return week_coursework

    def _get_course_task_index(self, course, today, week_start_date, school_year):
        """Get the db index of course tasks.

        This is based on the last completed coursework for the course.
        """
        # When this is the current week or the past, there is no need
        # to look into an index in the future.
        if week_start_date <= today:
            return 0

        this_week = Week(today)
        latest_coursework = (
            Coursework.objects.filter(student=self, course_task__course=course)
            .order_by("-completed_date")
            .first()
        )
        if latest_coursework and (
            this_week.first_day <= latest_coursework.completed_date
        ):
            start_date = latest_coursework.completed_date + datetime.timedelta(days=1)
        else:
            # When the student has no coursework yet, the counting should start
            # from the week start date relative to today.
            start_date = this_week.first_day

            # Clamp the start to the school year's start.
            # This is an edge case that appears when looking at future school years.
            if start_date < school_year.start_date:
                # This line is not covered, but the problem is tied to #495
                # Ignore the line in coverage for the moment.
                start_date = school_year.start_date  # pragma: no cover

        # TODO: Why is start_date not used? See #495

        last_school_day_this_week = school_year.last_school_day_for(this_week)
        is_current_week_active = today <= last_school_day_this_week
        if is_current_week_active:
            # During the active part of the week, tasks roll forward each day.
            # This means the unfinished work is everything from today to the end
            # of the last school day.
            remaining_tasks = school_year.get_task_count_in_range(
                course, today, last_school_day_this_week, self
            )
            completed_tasks = Coursework.objects.filter(
                student=self,
                course_task__course=course,
                completed_date__gte=today,
                completed_date__lte=last_school_day_this_week,
            ).count()
            unfinished_tasks_this_week = max(remaining_tasks - completed_tasks, 0)
        else:
            # On the weekend, don't count unfinished tasks and roll everything forward.
            unfinished_tasks_this_week = 0

        # Get the count of all the tasks between the current week
        # and the future week that the user wants to see.
        tasks_between = school_year.get_task_count_in_range(
            course,
            last_school_day_this_week + datetime.timedelta(days=1),
            week_start_date - datetime.timedelta(days=1),
            self,
        )
        return unfinished_tasks_this_week + tasks_between

    def get_last_coursework_date(
        self, week_coursework: dict, course: "Course"
    ) -> Optional[datetime.date]:
        """Get the last date of coursework if the course has any."""
        coursework_by_dates = week_coursework.get(course.id)
        return max(coursework_by_dates.keys()) if coursework_by_dates else None

    def get_day_coursework(self, day):
        """Get the coursework completed in the week.

        The data is in a dictionary for fast lookups.
        """
        day_coursework: dict = {}
        coursework_qs = (
            Coursework.objects.filter(student=self, completed_date=day)
            .order_by("course_task__id")
            .select_related("course_task")
        )
        for coursework in coursework_qs:
            course_id = coursework.course_task.course_id
            if course_id not in day_coursework:
                # It's possible for multiple coursework items to share the same
                # completion day because that's controlled by user input.
                day_coursework[course_id] = []

            day_coursework[course_id].append(coursework)

        return day_coursework

    def get_tasks_for(self, course):
        """Get all the tasks for the provided course.

        This includes any general or grade level specific task.
        """
        enrollment = self._enrollment_by_course_cache.get(course)
        if not enrollment:
            enrollment = (
                Enrollment.objects.filter(
                    student=self, grade_level__in=course.grade_levels.all()
                )
                .select_related("grade_level")
                .first()
            )
        if enrollment:
            return course.course_tasks.filter(
                Q(grade_level__isnull=True) | Q(grade_level=enrollment.grade_level)
            )
        else:
            return course.course_tasks.none()

    def get_incomplete_task_count_in_range(
        self, course, start_date, end_date, school_year
    ):
        """Get the count of incomplete tasks for a course.

        Be inclusive of start and end date.
        """
        task_count = school_year.get_task_count_in_range(
            course, start_date, end_date, self
        )
        coursework_count = Coursework.objects.filter(
            course_task__course=course,
            student=self,
            completed_date__range=[start_date, end_date],
        ).count()
        return task_count - coursework_count


class Enrollment(models.Model):
    """The association between a student and grade level"""

    id = HashidAutoField(
        primary_key=True, salt=f"enrollment{settings.HASHID_FIELD_SALT}"
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    grade_level = models.ForeignKey(
        "schools.GradeLevel", on_delete=models.CASCADE, related_name="enrollments"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "grade_level"], name="student_per_grade_level"
            )
        ]

    @classmethod
    def has_unenrolled_students(cls, school_year):
        """Check if the school year has unenrolled students."""
        return (
            cls.objects.filter(grade_level__school_year=school_year).count()
            < Student.objects.filter(school=school_year.school_id).count()
        )

    @classmethod
    def get_students_for_school_year(cls, school_year):
        """Get all the enrolled students in the school year."""
        enrollments = (
            cls.objects.filter(grade_level__school_year=school_year)
            .select_related("student")
            .order_by("student__first_name")
        )
        return [enrollment.student for enrollment in enrollments]


class Coursework(models.Model):
    """The work that student completes for course tasks"""

    class Meta:
        verbose_name_plural = "coursework"

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_task = models.ForeignKey("courses.CourseTask", on_delete=models.CASCADE)
    # Allow blank to delete coursework via an empty completed date in the form.
    completed_date = models.DateField(db_index=True, blank=True)


class Grade(models.Model):
    """An evaluation associated with graded work"""

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    graded_work = models.ForeignKey("courses.GradedWork", on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
