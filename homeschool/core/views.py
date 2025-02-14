from __future__ import annotations

import datetime

from dateutil.parser import parse
from denied.authorizers import any_authorized, staff_authorized
from denied.decorators import allow, authorize
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import render
from django.template.defaultfilters import pluralize
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.generic import CreateView, TemplateView

from homeschool.accounts.models import Account
from homeschool.core.schedules import Week
from homeschool.courses.forms import CourseForm, CourseTaskForm
from homeschool.courses.models import Course, CourseTask, GradedWork
from homeschool.notifications.models import Notification
from homeschool.schools.forms import GradeLevelForm, SchoolYearForm
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.students.models import Coursework, Enrollment, Grade, Student


@allow
def index(request):
    return render(request, "core/index.html", {})


@allow
def up(request):
    """A healthcheck to show when the app is up and able to respond to requests."""
    return render(request, "core/up.html", {})


@allow
def robots(request):
    return render(request, "core/robots.txt", {}, content_type="text/plain")


@allow
def sitemapindex(request):
    return render(request, "core/sitemapindex.xml", {}, content_type="text/xml")


@allow
def about(request):
    return render(request, "core/about.html", {})


@allow
def terms(request):
    return render(request, "core/terms.html", {})


@allow
def privacy(request):
    return render(request, "core/privacy.html", {})


@allow
def help(request):
    return render(request, "core/help.html", {"support_email": settings.SUPPORT_EMAIL})


@method_decorator(authorize(any_authorized), "dispatch")
class DashboardView(TemplateView):
    template_name = "core/app.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["nav_link"] = "dashboard"

        user = self.request.user

        today = user.get_local_today()
        day = self._get_day(today)
        self._set_week_dates_context(day, today, context)

        has_school_years = SchoolYear.objects.filter(school=user.school).exists()
        context["has_school_years"] = has_school_years

        has_students = Student.objects.filter(school=user.school).exists()
        context["has_students"] = has_students

        if has_school_years and has_students:
            self.get_week_context_data(context, day, today)
        else:
            context["has_tasks"] = CourseTask.objects.filter(
                course__grade_levels__school_year__school=user.school
            ).exists()

        context["show_whats_new"] = self.show_whats_new
        return context

    def _get_day(self, today: datetime.date) -> datetime.date:
        """Find the appropriate day to use for week calculation."""
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        day = self.kwargs.get("day")
        day = datetime.date(year, month, day) if year and month and day else today
        return day

    def _set_week_dates_context(self, day, today, context):
        """Set the dates for the primary week navigation element."""
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

    def get_week_context_data(self, context, day, today):
        """Get the context data for a week."""
        week = Week(day)

        school = self.request.user.school
        school_year = SchoolYear.get_year_for(self.request.user, day)

        if school_year:
            context["school_year"] = school_year

            # When the school year isn't in progress yet,
            # the offset calculations should come
            # relative to the start of the school year.
            if today < school_year.start_date:
                today = school_year.start_date

            # Check if this is the last week of the school year.
            # If so, there might be another school year immediately following this one.
            if school_year.end_date < week.last_day:
                self.get_next_school_year(context, today, week)
        else:
            self.get_next_school_year(context, today, week)

        context["schedules"] = self.get_schedules(school_year, today, week)

        if not context["schedules"]:
            future_school_year = (
                SchoolYear.objects.filter(school=school, start_date__gt=week.last_day)
                .order_by("start_date")
                .first()
            )
            if future_school_year:
                context["future_school_year"] = future_school_year
                future_week_start = Week(future_school_year.start_date).first_day
                context["future_school_year_week_url"] = reverse(
                    "core:weekly",
                    args=[
                        future_week_start.year,
                        future_week_start.month,
                        future_week_start.day,
                    ],
                )

        return context

    def get_schedules(
        self, school_year: SchoolYear | None, today: datetime.date, week: Week
    ) -> list:
        """Get the schedules for each student."""
        if school_year is None:
            return []

        return school_year.get_schedules(today, week)

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
            context["school_year"] = next_school_year

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


@method_decorator(authorize(any_authorized), "dispatch")
class DailyView(TemplateView):
    template_name = "core/daily.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["nav_link"] = "daily"

        user = self.request.user

        has_school_years = SchoolYear.objects.filter(school=user.school).exists()
        context["has_school_years"] = has_school_years

        has_students = Student.objects.filter(school=user.school).exists()
        context["has_students"] = has_students

        if has_school_years and has_students:
            self.get_daily_context(context)
        else:
            context["has_tasks"] = CourseTask.objects.filter(
                course__grade_levels__school_year__school=user.school
            ).exists()
        return context

    def get_daily_context(self, context):
        today = self.request.user.get_local_today()
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        day = self.kwargs.get("day")
        day = datetime.date(year, month, day) if year and month and day else today
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

        is_break_day = self.is_break_for_everyone(day, school_year)
        context["is_break_day"] = is_break_day
        context["schedules"] = self.get_schedules(school_year, today, day, is_break_day)
        return context

    def is_break_for_everyone(
        self, day: datetime.date, school_year: SchoolYear | None
    ) -> bool:
        """Check if this is a break day for all students."""
        if school_year is None:
            return False
        return all(
            school_year.is_break(day, student=student)
            for student in Student.get_students_for(school_year)
        )

    def get_schedules(
        self,
        school_year,
        today: datetime.date,
        day: datetime.date,
        is_break_for_everyone,
    ):
        """Get the schedules for each student."""
        schedules: list = []
        if not school_year or not school_year.runs_on(day) or is_break_for_everyone:
            return schedules

        for student in Student.get_students_for(school_year):
            schedule = self.get_student_schedule(student, today, day, school_year)
            schedules.append(schedule)

        return schedules

    def get_student_schedule(
        self, student, today: datetime.date, day: datetime.date, school_year
    ):
        """Get the daily schedule for the student."""
        is_break = school_year.is_break(day, student=student)
        schedule = {"student": student, "courses": [], "is_break": is_break}
        if is_break:
            return schedule

        courses = student.get_active_courses(school_year)
        day_coursework = student.get_day_coursework(day)
        completed_task_ids = list(
            Coursework.objects.filter(
                student=student, course_task__course__in=courses
            ).values_list("course_task_id", flat=True)
        )

        for course in courses:
            course_schedule = {"course": course}
            if course.id in day_coursework:
                course_schedule["coursework"] = day_coursework[course.id]
            elif course.runs_on(day):
                task_index = max(
                    student.get_incomplete_task_count_in_range(
                        course, today, day, school_year
                    )
                    - 1,
                    0,
                )
                # Doing this query in a loop is definitely an N+1 bug.
                # If it's possible to do a single query of all tasks
                # that groups by course then that would be better.
                # No need to over-optimize until that's a real issue.
                # I brought this up on the forum. It doesn't look like it's easy to fix.
                # https://forum.djangoproject.com/t/grouping-by-foreignkey-with-a-limit-per-group/979
                try:
                    course_schedule["task"] = (
                        student.get_tasks_for(course)
                        .exclude(id__in=completed_task_ids)
                        .select_related("graded_work", "resource")[task_index]
                    )
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
            student_id = parts[1]
            task_id = parts[2]

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
            message = (
                f"Completed {len(newly_complete_task_ids)} task{pluralized} "
                f"for {student.full_name}."
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
            message = (
                f"Undid {coursework_deleted} task{pluralized} for {student.full_name}."
            )
            messages.add_message(self.request, messages.SUCCESS, message)


class StartView(TemplateView):
    template_name = "core/start.html"

    @method_decorator(authorize(any_authorized))
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["support_email"] = settings.SUPPORT_EMAIL
        return context


@method_decorator(authorize(any_authorized), "dispatch")
class StartSchoolYearView(CreateView):
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


@method_decorator(authorize(any_authorized), "dispatch")
class StartGradeLevelView(CreateView):
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


@method_decorator(authorize(any_authorized), "dispatch")
class StartCourseView(CreateView):
    template_name = "core/start_course.html"
    form_class = CourseForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grade_level"] = self.grade_level
        if self.grade_level:
            context["course"] = (
                Course.objects.filter(grade_levels__in=[self.grade_level])
                .distinct()
                .first()
            )
        return context

    def get_success_url(self):
        return reverse("core:start-course-task")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school_year"] = (
            self.grade_level.school_year if self.grade_level else None
        )
        return kwargs

    @cached_property
    def grade_level(self) -> GradeLevel | None:
        return GradeLevel.objects.filter(
            school_year__school=self.request.user.school
        ).first()


@method_decorator(authorize(any_authorized), "dispatch")
class StartCourseTaskView(CreateView):
    template_name = "core/start_course_task.html"
    form_class = CourseTaskForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = (
            Course.objects.filter(
                grade_levels__school_year__school=self.request.user.school
            )
            .distinct()
            .first()
        )
        context["course"] = course
        if course:
            context["task"] = CourseTask.objects.filter(course=course).first()
        return context

    def get_success_url(self):
        return (
            reverse("schools:current_school_year") + f"?welcome={self.object.course.id}"
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


@authorize(staff_authorized)
def office_dashboard(request):
    """For back office stuff"""
    return render(request, "core/office/dashboard.html", {})


@authorize(staff_authorized)
def office_onboarding(request):
    """Show how new users are doing in the onboarding process."""
    now = timezone.now()
    trialing_users = [
        account.user
        for account in Account.objects.filter(status=Account.AccountStatus.TRIALING)
        .select_related("user")
        .order_by("-user")
    ]
    user_stats = []
    # Yeah, this is pretty dumb. Optimization is not important here.
    for user in trialing_users:
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        courses = Course.objects.filter(grade_levels__in=grade_levels).distinct()
        stats = {
            "user": user,
            "email_address": user.email,
            "school_years": SchoolYear.objects.filter(school__admin=user).count(),
            "grade_levels": len(grade_levels),
            "courses": len(courses),
            "tasks": CourseTask.objects.filter(course__in=courses).count(),
            "students": Student.objects.filter(school__admin=user).count(),
            "enrollments": Enrollment.objects.filter(
                student__school__admin=user
            ).count(),
            "tirekicker": False,
        }
        user_stats.append(stats)

        tirekicker_cutoff = user.date_joined + datetime.timedelta(days=7)
        data_keys = [
            "school_years",
            "grade_levels",
            "courses",
            "tasks",
            "students",
            "enrollments",
        ]
        if now > tirekicker_cutoff and all(stats[key] <= 1 for key in data_keys):
            stats["tirekicker"] = True

    context = {
        "user_stats": user_stats,
        "tirekicker_count": len([u for u in user_stats if u["tirekicker"]]),
    }
    return render(request, "core/office/onboarding.html", context)


@authorize(staff_authorized)
def boom(request):
    """This is for checking error handling (like Sentry)."""
    raise Exception("Is this thing on?")


@authorize(staff_authorized)
def social_image(request):
    """Render a view to create any social images."""
    return render(request, "core/office/social_image.html", {})


@allow
def handle_403(request, exception=None):
    """Handle 403 errors and display them."""
    return render(request, "403.html", {}, status=403)


@allow
def handle_404(request, exception=None):
    """Handle 404 errors and display them."""
    return render(request, "404.html", {}, status=404)


@allow
def handle_500(request):
    """Handle 500 errors and display them."""
    return render(request, "500.html", {}, status=500)


@allow
def favicon(request):
    return HttpResponsePermanentRedirect(static("favicon/favicon.ico"))
