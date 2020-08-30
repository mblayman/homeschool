import datetime
import uuid

from django.db import models
from django.db.models import Q

from homeschool.core.schedules import Week


class Student(models.Model):
    """The learner"""

    school = models.ForeignKey(
        "schools.School", on_delete=models.CASCADE, related_name="students"
    )
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)

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
        courses = self.get_courses(school_year)
        week_coursework = self.get_week_coursework(week)

        week_start_date = week.first_day
        week_end_date = school_year.last_school_day_for(week)
        completed_task_ids = list(
            Coursework.objects.filter(
                student=self, course_task__course__in=courses
            ).values_list("course_task_id", flat=True)
        )
        task_limit = len(week_dates)
        schedule: dict = {"student": self, "courses": []}
        for course in courses:
            if week_end_date > today and not course.is_running:
                continue

            course_schedule = {"course": course, "days": []}

            course_tasks = []
            # Only show tasks on current or future weeks.
            if week_end_date >= today:
                task_index = 0
                if week_start_date > today:
                    task_index = self.get_future_course_task_index(
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

            for week_date in week_dates:
                course_schedule_item = {"week_date": week_date}
                course_schedule["days"].append(course_schedule_item)

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
                elif course.runs_on(week_date) and course_tasks:
                    course_schedule_item["task"] = course_tasks.pop()
            schedule["courses"].append(course_schedule)
        return schedule

    def get_courses(self, school_year):
        """Get the courses from the school year."""
        enrollment = Enrollment.objects.filter(
            student=self, grade_level__in=school_year.grade_levels.all()
        ).first()
        if enrollment:
            # This looks goofy, but it operates under the assumption
            # school year did all the prefetching on grade levels and courses.
            for grade_level in school_year.grade_levels.all():
                if grade_level.id == enrollment.grade_level_id:
                    return list(grade_level.courses.all())
        return []

    def get_week_coursework(self, week):
        """Get the coursework completed in the week.

        The data is in a dictionary for fast lookups.
        """
        week_coursework: dict = {}
        coursework_qs = Coursework.objects.filter(
            student=self, completed_date__range=(week.first_day, week.last_day)
        ).select_related("course_task")
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

    def get_future_course_task_index(self, course, today, week_start_date, school_year):
        """Get the db index of course tasks for future weeks.

        This is based on the last completed coursework for the course.
        """
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
                start_date = school_year.start_date

        # Adjust the starting index for future weeks to account for any unfinished tasks
        # from the current week.
        unfinished_task_count_this_week = 0
        if school_year.last_school_day_for(this_week) < today:
            unfinished_task_count_this_week = course.get_task_count_in_range(
                start_date, today
            )

        return (
            course.get_task_count_in_range(
                start_date, week_start_date - datetime.timedelta(days=1)
            )
            - unfinished_task_count_this_week
        )

    def get_day_coursework(self, day):
        """Get the coursework completed in the week.

        The data is in a dictionary for fast lookups.
        """
        day_coursework: dict = {}
        coursework_qs = Coursework.objects.filter(
            student=self, completed_date=day
        ).select_related("course_task")
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


class Enrollment(models.Model):
    """The association between a student and grade level"""

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    grade_level = models.ForeignKey("schools.GradeLevel", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "grade_level"], name="student_per_grade_level"
            )
        ]


class Coursework(models.Model):
    """The work that student completes for course tasks"""

    class Meta:
        verbose_name_plural = "coursework"

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_task = models.ForeignKey("courses.CourseTask", on_delete=models.CASCADE)
    completed_date = models.DateField(db_index=True)


class Grade(models.Model):
    """An evaluation associated with graded work"""

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    graded_work = models.ForeignKey("courses.GradedWork", on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)
    score = models.PositiveIntegerField(default=0)
