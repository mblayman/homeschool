import datetime

from dateutil.parser import parse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, TemplateView

from homeschool.core.schedules import Week
from homeschool.courses.models import Course, GradedWork
from homeschool.notifications.models import Notification
from homeschool.schools.forms import GradeLevelForm, SchoolYearForm
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.students.models import Coursework, Grade, Student


class IndexView(TemplateView):
    template_name = "core/index.html"


class AppView(LoginRequiredMixin, TemplateView):
    template_name = "core/app.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        today = self.request.user.get_local_today()
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        day = self.kwargs.get("day")
        if year and month and day:
            day = datetime.date(year, month, day)
        else:
            day = today
        context["day"] = day

        week = Week(day)

        # Fix the corner case when the weekly view is used and today falls in the week.
        # In that scenario, don't point at the first day of the week
        # since it messes with the UI.
        if week.first_day <= today <= week.last_day:
            context["day"] = today

        context["first_day"], context["last_day"] = week.first_day, week.last_day
        context["previous_week_date"] = context["first_day"] - datetime.timedelta(
            days=7
        )
        context["next_week_date"] = context["first_day"] + datetime.timedelta(days=7)

        school_year = (
            SchoolYear.objects.filter(
                school=self.request.user.school, start_date__lte=day, end_date__gte=day
            )
            .prefetch_related("grade_levels")
            .first()
        )

        if school_year:
            # When the school year isn't in progress yet,
            # the offset calculations should come
            # relative to the start of the school year.
            if today < school_year.start_date:
                today = school_year.start_date

            context["week_dates"] = self.build_week_dates(school_year, week)

            # Check if this is the last week of the school year.
            # If so, there might be another school year immediately following this one.
            if school_year.end_date < week.last_day:
                self.get_next_school_year(context, today, week)
        else:
            self.get_next_school_year(context, today, week)

        context["schedules"] = self.get_schedules(school_year, today, week)
        context["show_whats_new"] = self.show_whats_new
        return context

    def build_week_dates(self, school_year, week):
        """Build the week dates for the context."""
        week_dates = []
        for week_date in school_year.get_week_dates_for(week):
            school_break = school_year.get_break(week_date)
            week_date_data = {"date": week_date, "school_break": school_break}
            if school_break:
                week_date_data["date_type"] = school_break.get_date_type(week_date)
            week_dates.append(week_date_data)
        return week_dates

    def get_schedules(self, school_year, today, week):
        """Get the schedules for each student."""
        if school_year is None:
            return []

        return [
            student.get_week_schedule(school_year, today, week)
            for student in Student.get_students_for(school_year)
        ]

    def get_next_school_year(self, context, today, week):
        """Get the next year.

        This is needed at the boundaries of the school year.
        """
        # Check if this is the first week of the school year.
        # If so, the first day of the week might be before the school years starts.
        # In that scenario, try to get the school year by looking ahead.
        next_school_year = (
            SchoolYear.objects.filter(
                school=self.request.user.school, start_date__range=week
            )
            .prefetch_related("grade_levels", "grade_levels__courses")
            .first()
        )
        if next_school_year:
            context["next_year_week_dates"] = self.build_week_dates(
                next_school_year, week
            )

        # When the school year isn't in progress yet,
        # the offset calculations should come
        # relative to the start of the school year.
        if next_school_year and today < next_school_year.start_date:
            today = next_school_year.start_date

        context["next_year_schedules"] = self.get_schedules(
            next_school_year, today, week
        )

    @property
    def show_whats_new(self):
        """Check if the "What's New?" badge should be displayed."""
        user = self.request.user
        return (
            user.profile.wants_announcements
            and Notification.objects.filter(
                user=user, status=Notification.NotificationStatus.UNREAD
            ).exists()
        )


class DailyView(LoginRequiredMixin, TemplateView):
    template_name = "core/daily.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        today = self.request.user.get_local_today()
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        day = self.kwargs.get("day")
        if year and month and day:
            day = datetime.date(year, month, day)
        else:
            day = today
        context["day"] = day

        first_day = Week(day).first_day
        context["weekly_url"] = reverse(
            "core:weekly", args=[first_day.year, first_day.month, first_day.day]
        )
        school_year = (
            SchoolYear.objects.filter(
                school=self.request.user.school, start_date__lte=day, end_date__gte=day
            )
            .prefetch_related("grade_levels")
            .first()
        )

        # When the school year isn't in progress yet,
        # the offset calculations should come
        # relative to the start of the school year.
        if school_year and today < school_year.start_date:
            today = school_year.start_date

        # Set previous and next days navigation.
        if school_year:
            context["yesterday"] = school_year.get_previous_day_from(day)
            context["ereyesterday"] = school_year.get_previous_day_from(
                context["yesterday"]
            )
            context["tomorrow"] = school_year.get_next_day_from(day)
            context["overmorrow"] = school_year.get_next_day_from(context["tomorrow"])
        else:
            context["ereyesterday"] = day - datetime.timedelta(days=2)
            context["yesterday"] = day - datetime.timedelta(days=1)
            context["tomorrow"] = day + datetime.timedelta(days=1)
            context["overmorrow"] = day + datetime.timedelta(days=2)

        context["is_break_day"] = bool(school_year and school_year.is_break(day))
        context["schedules"] = self.get_schedules(school_year, today, day)
        return context

    def get_schedules(self, school_year, today, day):
        """Get the schedules for each student."""
        schedules: list = []
        if not school_year or not school_year.runs_on(day) or school_year.is_break(day):
            return schedules

        for student in Student.get_students_for(school_year):
            schedule = self.get_student_schedule(student, today, day, school_year)
            schedules.append(schedule)

        return schedules

    def get_student_schedule(self, student, today, day, school_year):
        """Get the daily schedule for the student."""
        courses = student.get_active_courses(school_year)
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
                task_index = max(
                    school_year.get_task_count_in_range(course, today, day) - 1, 0
                )
                # Doing this query in a loop is definitely an N+1 bug.
                # If it's possible to do a single query of all tasks
                # that groups by course then that would be better.
                # No need to over-optimize until that's a real issue.
                # I brought this up on the forum. It doesn't look like it's easy to fix.
                # https://forum.djangoproject.com/t/grouping-by-foreignkey-with-a-limit-per-group/979
                try:
                    course_schedule["task"] = student.get_tasks_for(course).exclude(
                        id__in=completed_task_ids
                    )[task_index]
                except IndexError:
                    course_schedule["no_scheduled_task"] = True
            schedule["courses"].append(course_schedule)
        return schedule

    def post(self, request, *args, **kwargs):
        """Process students' work."""
        completed_date = timezone.now().date()
        if "completed_date" in request.POST:
            completed_date = parse(request.POST["completed_date"])

        tasks_by_student = self.get_task_completions_by_student(request.POST)
        work_to_grade = False
        if tasks_by_student:
            for student_id, tasks in tasks_by_student.items():
                student = request.user.school.students.filter(id=student_id).first()
                if student:
                    has_work_to_grade = self.mark_completion(
                        student, tasks, completed_date
                    )
                    if has_work_to_grade:
                        work_to_grade = True

        if work_to_grade:
            success_url = self.get_grade_url()
        else:
            success_url = request.GET.get("next", reverse("core:daily"))
        return HttpResponseRedirect(success_url)

    def get_task_completions_by_student(self, post_data):
        """Parse out the tasks."""
        tasks: dict = {}
        for key, value in post_data.items():
            if not key.startswith("task"):
                continue
            parts = key.split("-")
            student_id = int(parts[1])
            task_id = int(parts[2])

            if student_id not in tasks:
                tasks[student_id] = {"complete": [], "incomplete": []}

            category = "complete" if value == "on" else "incomplete"
            tasks[student_id][category].append(task_id)
        return tasks

    def get_grade_url(self):
        grade_url = reverse("students:grade")
        next_url = self.request.GET.get("next", reverse("core:daily"))
        return f"{grade_url}?next={next_url}"

    def mark_completion(self, student, tasks, completed_date):
        """Mark completed tasks or clear already complete tasks."""
        has_work_to_grade = self.process_complete_tasks(
            student, tasks["complete"], completed_date
        )
        self.process_incomplete_tasks(student, tasks["incomplete"])
        return has_work_to_grade

    def process_complete_tasks(self, student, complete_task_ids, completed_date):
        """Add coursework for any tasks that do not have it."""
        has_work_to_grade = False
        existing_complete_task_ids = set(
            Coursework.objects.filter(
                student=student, course_task__in=complete_task_ids
            ).values_list("course_task_id", flat=True)
        )
        newly_complete_task_ids = set(complete_task_ids) - existing_complete_task_ids
        if newly_complete_task_ids:
            new_coursework = []
            for task_id in newly_complete_task_ids:
                new_coursework.append(
                    Coursework(
                        student=student,
                        course_task_id=task_id,
                        completed_date=completed_date,
                    )
                )
            Coursework.objects.bulk_create(new_coursework)

            pluralized = pluralize(len(newly_complete_task_ids))
            message = "Completed {} task{} for {}.".format(
                len(newly_complete_task_ids), pluralized, student.full_name
            )
            messages.add_message(self.request, messages.SUCCESS, message)

            graded_work_ids = set(
                GradedWork.objects.filter(
                    course_task__in=newly_complete_task_ids
                ).values_list("id", flat=True)
            )
            already_graded_work_ids = set(
                Grade.objects.filter(
                    student=student, graded_work__in=graded_work_ids
                ).values_list("graded_work_id", flat=True)
            )
            has_work_to_grade = bool(graded_work_ids - already_graded_work_ids)

        return has_work_to_grade

    def process_incomplete_tasks(self, student, incomplete_task_ids):
        """Remove any coursework for tasks that are marked as incomplete."""
        delete_info = Coursework.objects.filter(
            student=student, course_task__in=incomplete_task_ids
        ).delete()
        coursework_deleted = delete_info[0]
        if coursework_deleted > 0:
            pluralized = pluralize(coursework_deleted)
            message = "Undid {} task{} for {}.".format(
                coursework_deleted, pluralized, student.full_name
            )
            messages.add_message(self.request, messages.SUCCESS, message)


class StartView(LoginRequiredMixin, TemplateView):
    template_name = "core/start.html"

    def dispatch(self, *args, **kwargs):
        # Remove alert messages contributed by django-allauth during sign up
        # that distract from the onboarding start page.
        # Removing from the incoming request prevents Django from rendering messages
        # on *this* view.
        self.request.COOKIES.pop("messages", "")

        response = super().dispatch(*args, **kwargs)

        # Tell the browser to remove any existing messages.
        # Removing from the response prevents Django from rendering messages
        # on the *next* view.
        response.delete_cookie("messages")

        return response


class StartSchoolYearView(LoginRequiredMixin, CreateView):
    template_name = "core/start_school_year.html"
    form_class = SchoolYearForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["school_year"] = SchoolYear.objects.filter(
            school=self.request.user.school
        ).first()
        return context

    def get_success_url(self):
        return reverse("core:start-grade-level")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        if "data" in kwargs:
            # Since this view is for easy onboarding,
            # set a reasonable standard week.
            # The QueryDict is immutable so it must be copied to update it.
            data = kwargs["data"].copy()
            data.update(
                {
                    "monday": True,
                    "tuesday": True,
                    "wednesday": True,
                    "thursday": True,
                    "friday": True,
                }
            )
            kwargs["data"] = data
        return kwargs


class StartGradeLevelView(LoginRequiredMixin, CreateView):
    template_name = "core/start_grade_level.html"
    form_class = GradeLevelForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grade_level"] = GradeLevel.objects.filter(
            school_year__school=self.request.user.school
        ).first()
        context["school_year"] = SchoolYear.objects.filter(
            school=self.request.user.school
        ).first()
        return context

    def get_success_url(self):
        return reverse("core:start-course")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class StartCourseView(LoginRequiredMixin, TemplateView):
    template_name = "core/start_course.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grade_level = GradeLevel.objects.filter(
            school_year__school=self.request.user.school
        ).first()
        context["grade_level"] = grade_level
        if grade_level:
            context["course"] = (
                Course.objects.filter(grade_levels__in=[context["grade_level"]])
                .distinct()
                .first()
            )
        return context


class StartCourseTaskView(LoginRequiredMixin, TemplateView):
    template_name = "core/start_course.html"


@staff_member_required
def boom(request):
    """This is for checking error handling (like Rollbar)."""
    raise Exception("Is this thing on?")


def handle_500(request):
    """Handle 500 errors and display them."""
    return render(request, "500.html", {}, status=500)
