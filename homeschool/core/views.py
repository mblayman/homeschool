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

        # This is UTC so it is not localized to the user's timezone.
        # That may lead to funny results in the evening.
        today = timezone.now().date()
        context["today"] = today

        week = self.get_week_boundaries(today)
        context["monday"], context["sunday"] = week

        school_year = (
            SchoolYear.objects.filter(start_date__lte=today, end_date__gte=today)
            .prefetch_related("grade_levels", "grade_levels__courses")
            .first()
        )

        week_dates = []
        if school_year:
            week_dates = school_year.get_week_dates_for(week)
        context["week_dates"] = week_dates

        context["schedules"] = self.get_schedules(school_year, week, week_dates)
        return context

    def get_week_boundaries(self, today):
        """Get the Monday and Sunday that bound today."""
        monday = today + relativedelta(weekday=MO(-1))
        sunday = today + relativedelta(weekday=SU(+1))
        return monday, sunday

    def get_schedules(self, school_year, week, week_dates):
        """Get the schedules for each student."""
        schedules = []
        if school_year is None:
            return schedules

        for student in self.request.user.school.students.all():
            courses = student.get_courses(school_year)
            week_coursework = student.get_week_coursework(week)
            schedule = self.get_student_schedule(
                student, week_dates, courses, week_coursework
            )
            schedules.append(schedule)

        return schedules

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
                course_schedule_item = {"week_date": week_date}
                if (
                    course.id in week_coursework
                    and week_date in week_coursework[course.id]
                ):
                    coursework_list = week_coursework[course.id][week_date]
                    course_schedule_item["coursework"] = coursework_list
                elif course.runs_on(week_date) and course_tasks:
                    course_schedule_item["task"] = course_tasks.pop()
                course_schedule["days"].append(course_schedule_item)
            schedule["courses"].append(course_schedule)
        return schedule


class DailyView(LoginRequiredMixin, TemplateView):
    template_name = "core/daily.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # This is UTC so it is not localized to the user's timezone.
        # That may lead to funny results in the evening.
        today = timezone.now().date()
        context["day"] = today

        school_year = (
            SchoolYear.objects.filter(start_date__lte=today, end_date__gte=today)
            .prefetch_related("grade_levels", "grade_levels__courses")
            .first()
        )

        context["schedules"] = self.get_schedules(school_year, today)
        return context

    def get_schedules(self, school_year, day):
        """Get the schedules for each student."""
        schedules = []
        if not school_year:
            return schedules

        if not school_year.runs_on(day):
            return schedules

        for student in self.request.user.school.students.all():
            courses = student.get_courses(school_year)
            schedule = self.get_student_schedule(student, day, courses)
            schedules.append(schedule)

        return schedules

    def get_student_schedule(self, student, day, courses):
        """Get the daily schedule for the student."""
        day_coursework = student.get_day_coursework(day)
        completed_task_ids = list(
            Coursework.objects.filter(
                student=student, course_task__course__in=courses
            ).values_list("course_task_id", flat=True)
        )
        schedule = {"student": student, "courses": []}
        for course in courses:
            course_schedule = {"course": course}
            if course.id in day_coursework:
                course_schedule["coursework"] = day_coursework[course.id]
            elif course.runs_on(day):
                # Doing this query in a loop is definitely an N+1 bug.
                # If it's possible to do a single query of all tasks
                # that groups by course then that would be better.
                # No need to over-optimize until that's a real issue.
                # I brought this up on the forum. It doesn't look like it's easy to fix.
                # https://forum.djangoproject.com/t/grouping-by-foreignkey-with-a-limit-per-group/979
                course_task = course.course_tasks.exclude(
                    id__in=completed_task_ids
                ).first()
                course_schedule["task"] = course_task
            schedule["courses"].append(course_schedule)
        return schedule
