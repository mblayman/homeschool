from dateutil.relativedelta import MO, SU, relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic.base import TemplateView

from homeschool.schools.models import SchoolYear
from homeschool.students.models import Coursework


class IndexView(TemplateView):
    template_name = "core/index.html"


class AppView(LoginRequiredMixin, TemplateView):
    template_name = "core/app.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        today = timezone.now().date()
        week = self.get_week_boundaries(today)
        context["monday"], context["sunday"] = week

        school_year = (
            SchoolYear.objects.filter(start_date__lte=today, end_date__gte=today)
            .prefetch_related("grade_levels", "grade_levels__courses")
            .first()
        )

        context["schedules"] = self.get_schedules(school_year, week)
        return context

    def get_week_boundaries(self, today):
        """Get the Monday and Sunday that bound today."""
        monday = today + relativedelta(weekday=MO(-1))
        sunday = today + relativedelta(weekday=SU(+1))
        return monday, sunday

    def get_schedules(self, school_year, week):
        """Get the schedules for each student."""
        schedules = []
        if school_year is None:
            return schedules

        week_dates = school_year.get_week_dates_for(week)
        for student in self.request.user.school.students.all():
            courses = student.get_courses(school_year)
            week_coursework = self.get_student_week_coursework(student, courses, week)
            schedule = self.get_student_schedule(
                student, week_dates, courses, week_coursework
            )
            schedules.append(schedule)

        return schedules

    def get_student_week_coursework(self, student, courses, week):
        """Get the student's week coursework in dict for fast lookup."""
        week_coursework = {}
        coursework_qs = Coursework.objects.filter(
            student=student, course_task__course__in=courses, completed_date__range=week
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

    def get_student_schedule(self, student, week_dates, courses, week_coursework):
        """Get the schedule.

        Each student will get a list of courses, filled with each day.
        Empty slots will contain None.
        """
        completed_task_ids = list(
            Coursework.objects.filter(
                student=student, course_task__course__in=courses
            ).values_list("course_task_id", flat=True)
        )
        task_limit = len(week_dates)
        schedule = {"student": student, "courses": []}
        for course in courses:
            course_schedule = {"course": course, "days": []}
            # Doing this query in a loop is definitely an N+1 bug.
            # If it's possible to do a single query of all tasks
            # that groups by course then that would be better.
            # No need to over-optimize until that's a real issue.
            # I brought this up on the forum. It doesn't look like it's easy to fix.
            # https://forum.djangoproject.com/t/grouping-by-foreignkey-with-a-limit-per-group/979
            course_tasks = list(
                course.course_tasks.exclude(id__in=completed_task_ids)[:task_limit]
            )
            course_tasks.reverse()
            for week_date in week_dates:
                if (
                    course.id in week_coursework
                    and week_date in week_coursework[course.id]
                ):
                    coursework_list = week_coursework[course.id][week_date]
                    course_schedule["days"].append({"coursework": coursework_list})
                    continue

                if course.runs_on(week_date):
                    if course_tasks:
                        course_schedule["days"].append({"task": course_tasks.pop()})
                    else:
                        # There may be no tasks left to pull from.
                        course_schedule["days"].append(None)
                else:
                    course_schedule["days"].append(None)
            schedule["courses"].append(course_schedule)
        return schedule
