import datetime
import uuid
from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from homeschool.courses.models import CourseResource
from homeschool.students.models import Coursework, Enrollment, Grade

from .forecaster import Forecaster
from .forms import GradeLevelForm, SchoolBreakForm, SchoolYearForm
from .models import GradeLevel, SchoolBreak, SchoolYear
from .year_calendar import YearCalendar


class CurrentSchoolYearView(LoginRequiredMixin, View):
    """Show the most relevant current school year.

    That may be an in-progress school year or a future school year
    if the user is in a planning phase.
    """

    def get(self, request, *args, **kwargs):
        user = self.request.user
        school_year = SchoolYear.get_current_year_for(user)

        # When there is no school year, send them to the list page
        # so the user can see where to create a new school year.
        if not school_year:
            return HttpResponseRedirect(reverse("schools:school_year_list"))

        return SchoolYearDetailView.as_view()(request, uuid=school_year.uuid)


class SchoolYearCreateView(LoginRequiredMixin, CreateView):
    template_name = "schools/schoolyear_form.html"
    form_class = SchoolYearForm
    initial = {
        "monday": True,
        "tuesday": True,
        "wednesday": True,
        "thursday": True,
        "friday": True,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        return context

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.object.uuid])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class SchoolYearDetailView(LoginRequiredMixin, DetailView):
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return SchoolYear.objects.filter(school__admin=user).prefetch_related(
            "breaks", "grade_levels"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_link"] = "school_year"

        today = self.request.user.get_local_today()
        context["calendar"] = YearCalendar(self.object, today).build(
            show_all=bool(self.request.GET.get("show_all_months"))
        )
        context["is_in_school_year"] = self.object.contains(today)
        context["grade_levels"] = []
        for grade_level in self.object.grade_levels.all():
            context["grade_levels"].append(
                {
                    "grade_level": grade_level,
                    "courses": grade_level.get_ordered_courses(),
                    "has_students": Enrollment.objects.filter(
                        grade_level=grade_level
                    ).exists(),
                }
            )
        return context


class SchoolYearEditView(LoginRequiredMixin, UpdateView):
    form_class = SchoolYearForm
    template_name = "schools/schoolyear_form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return SchoolYear.objects.filter(school=user.school)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        return {
            "sunday": self.object.runs_on(SchoolYear.SUNDAY),
            "monday": self.object.runs_on(SchoolYear.MONDAY),
            "tuesday": self.object.runs_on(SchoolYear.TUESDAY),
            "wednesday": self.object.runs_on(SchoolYear.WEDNESDAY),
            "thursday": self.object.runs_on(SchoolYear.THURSDAY),
            "friday": self.object.runs_on(SchoolYear.FRIDAY),
            "saturday": self.object.runs_on(SchoolYear.SATURDAY),
        }

    def get_success_url(self):
        return reverse(
            "schools:school_year_detail", kwargs={"uuid": self.kwargs["uuid"]}
        )


class SchoolYearForecastView(LoginRequiredMixin, TemplateView):
    template_name = "schools/schoolyear_forecast.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        school_year = get_object_or_404(
            SchoolYear.objects.filter(school__admin=user), uuid=self.kwargs["uuid"]
        )
        context["schoolyear"] = school_year

        enrollments = Enrollment.objects.filter(
            grade_level__school_year=school_year
        ).select_related("grade_level", "student")
        students = []
        for enrollment in enrollments:
            student_info = {"student": enrollment.student, "courses": []}

            for course in enrollment.grade_level.get_ordered_courses():
                forecaster = Forecaster()
                course_info = {
                    "course": course,
                    "last_forecast_date": forecaster.get_last_forecast_date(
                        enrollment.student, course
                    ),
                }
                student_info["courses"].append(course_info)

            students.append(student_info)

        context["students"] = students
        return context


class SchoolYearListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        user = self.request.user
        return SchoolYear.objects.filter(school__admin=user).order_by("-start_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_link"] = "school_year"
        return context


class GradeLevelCreateView(LoginRequiredMixin, CreateView):
    form_class = GradeLevelForm
    template_name = "schools/gradelevel_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        user = self.request.user
        context["school_year"] = get_object_or_404(
            SchoolYear.objects.filter(school__admin=user), uuid=self.kwargs["uuid"]
        )
        return context

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.kwargs["uuid"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class GradeLevelUpdateView(LoginRequiredMixin, UpdateView):
    form_class = GradeLevelForm
    template_name = "schools/gradelevel_form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return GradeLevel.objects.filter(
            school_year__school=user.school
        ).select_related("school_year")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["school_year"] = self.object.school_year
        return context

    def get_success_url(self):
        return reverse(
            "schools:school_year_detail", args=[self.object.school_year.uuid]
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


def move_course(user, grade_level_uuid, course_uuid, direction):
    """Move the course ordering in the specified direction."""
    grade_level = get_object_or_404(
        GradeLevel, uuid=grade_level_uuid, school_year__school__admin=user
    )
    through = get_object_or_404(
        grade_level.courses.through,
        grade_level__uuid=grade_level_uuid,
        course__uuid=course_uuid,
    )
    getattr(through, direction)()
    return HttpResponseRedirect(
        reverse("schools:grade_level_edit", args=[grade_level_uuid])
    )


@login_required
@require_POST
def move_course_down(request, uuid, course_uuid):
    """Move a course down in the ordering."""
    return move_course(request.user, uuid, course_uuid, "down")


@login_required
@require_POST
def move_course_up(request, uuid, course_uuid):
    """Move a course up in the ordering."""
    return move_course(request.user, uuid, course_uuid, "up")


class SchoolBreakCreateView(LoginRequiredMixin, CreateView):
    form_class = SchoolBreakForm
    template_name = "schools/schoolbreak_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        user = self.request.user
        context["school_year"] = get_object_or_404(
            SchoolYear.objects.filter(school__admin=user), uuid=self.kwargs["uuid"]
        )
        return context

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.kwargs["uuid"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class SchoolBreakUpdateView(LoginRequiredMixin, UpdateView):
    form_class = SchoolBreakForm
    template_name = "schools/schoolbreak_form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return SchoolBreak.objects.filter(
            school_year__school=user.school
        ).select_related("school_year")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["school_year"] = self.object.school_year
        return context

    def get_success_url(self):
        return reverse(
            "schools:school_year_detail", args=[self.object.school_year.uuid]
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class SchoolBreakDeleteView(LoginRequiredMixin, DeleteView):
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return SchoolBreak.objects.filter(
            school_year__school=user.school
        ).select_related("school_year")

    def get_success_url(self):
        return reverse(
            "schools:school_year_detail", args=[self.object.school_year.uuid]
        )


class ReportsIndexView(LoginRequiredMixin, TemplateView):
    template_name = "schools/reports_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_link"] = "reports"

        user = self.request.user
        context["enrollments"] = (
            Enrollment.objects.filter(grade_level__school_year__school__admin=user)
            .select_related("student", "grade_level", "grade_level__school_year")
            .order_by("-grade_level__school_year__start_date", "student")
        )
        return context


class ProgressReportView(LoginRequiredMixin, TemplateView):
    template_name = "schools/progress_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "student", "grade_level", "grade_level__school_year"
            ),
            student__uuid=self.kwargs["student_uuid"],
            grade_level__school_year__uuid=self.kwargs["uuid"],
            grade_level__school_year__school=user.school,
        )
        context["grade_level"] = enrollment.grade_level
        context["school_year"] = enrollment.grade_level.school_year
        context["student"] = enrollment.student

        course_uuid = self._get_course_uuid()
        if course_uuid:
            qs_filter = Q(graded_work__course_task__course__uuid=course_uuid)
        else:
            qs_filter = Q(
                graded_work__course_task__course__grade_levels__in=[
                    enrollment.grade_level
                ]
            )

        grades = (
            Grade.objects.filter(qs_filter, student=enrollment.student)
            # Include secondary ordering so tasks are ordered in the course.
            .order_by(
                "graded_work__course_task__course", "graded_work__course_task"
            ).select_related(
                "graded_work__course_task", "graded_work__course_task__course"
            )
        )

        self._mixin_coursework(grades, enrollment.student)
        context["courses"] = self._build_courses_info(grades)
        return context

    def _get_course_uuid(self):
        """Get a course UUID if a valid entry is in the querystring."""
        course_uuid = self.request.GET.get("course")
        if course_uuid:
            try:
                uuid.UUID(course_uuid)
            except ValueError:
                # If the UUID doesn't smell right, skip filtering.
                return ""
        return course_uuid

    def _mixin_coursework(self, grades, student):
        """Mix in the coursework for the grades.

        Coursework is added to the grades to display the completed dates.
        It is possible for a user to add a grade without the student finishing the task
        so the coursework can be None.
        """
        tasks = [grade.graded_work.course_task for grade in grades]
        coursework_by_task_id = {
            coursework.course_task_id: coursework
            for coursework in Coursework.objects.filter(
                student=student, course_task__in=tasks
            )
        }
        for grade in grades:
            grade.coursework = coursework_by_task_id.get(
                grade.graded_work.course_task_id
            )

    def _build_courses_info(self, grades):
        """Regroup the grades into an appropriate display structure for the template.

        Grades must be sorted by course.
        """
        if not grades:
            return []

        courses = []
        course = None
        course_info = {}
        for grade in grades:
            next_course = grade.graded_work.course_task.course
            if course != next_course:
                # Don't compute average until a course is collected.
                # On the first iteration when course is None, nothing is collected yet.
                if course is not None:
                    self._compute_course_average(course_info)
                course = next_course
                course_info = {"course": course, "grades": [grade]}
                courses.append(course_info)
            else:
                course_info["grades"].append(grade)

        # Compute average of last course to catch the edge case.
        self._compute_course_average(course_info)
        return courses

    def _compute_course_average(self, course_info):
        """Compute the average for the course based on collected grades."""
        grades = course_info["grades"]
        average = sum(grade.score for grade in grades) / len(grades)
        # Sane rounding.
        course_info["course_average"] = int(Decimal(average).quantize(0, ROUND_HALF_UP))


class ResourceReportView(LoginRequiredMixin, TemplateView):
    template_name = "schools/resource_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "student", "grade_level", "grade_level__school_year"
            ),
            student__uuid=self.kwargs["student_uuid"],
            grade_level__school_year__uuid=self.kwargs["uuid"],
            grade_level__school_year__school=user.school,
        )
        context["grade_level"] = enrollment.grade_level
        context["school_year"] = enrollment.grade_level.school_year
        context["student"] = enrollment.student
        context["resources"] = (
            CourseResource.objects.filter(
                course__grade_levels__in=[enrollment.grade_level]
            )
            .select_related("course")
            .order_by("course")
        )
        return context


class AttendanceReportView(LoginRequiredMixin, TemplateView):
    template_name = "schools/attendance_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "student", "grade_level", "grade_level__school_year"
            ),
            uuid=self.kwargs["uuid"],
            grade_level__school_year__school=user.school,
        )
        context["grade_level"] = enrollment.grade_level
        context["school_year"] = enrollment.grade_level.school_year
        context["student"] = enrollment.student
        context["school_dates"] = self._build_school_dates(enrollment)
        context["total_days_attended"] = sum(
            1 for school_date in context["school_dates"] if school_date["attended"]
        )
        return context

    def _build_school_dates(self, enrollment):
        """Collect all the school dates in the year to the end or today."""
        dates_with_work = set(
            Coursework.objects.filter(
                student=enrollment.student,
                course_task__course__grade_levels__in=[enrollment.grade_level],
            ).values_list("completed_date", flat=True)
        )
        school_dates = []
        school_year = enrollment.grade_level.school_year
        school_date = school_year.start_date
        end_date = min(school_year.end_date, self.request.user.get_local_today())
        while school_date <= end_date:
            school_dates.append(
                {
                    "date": school_date,
                    "is_school_day": school_year.runs_on(school_date),
                    "is_break": school_year.is_break(school_date),
                    "attended": school_date in dates_with_work,
                }
            )
            school_date += datetime.timedelta(days=1)
        return school_dates
