from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
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
from homeschool.students.models import Enrollment, Grade

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


class SchoolYearListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        user = self.request.user
        return SchoolYear.objects.filter(school__admin=user).order_by("-start_date")


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
        context["grades"] = (
            Grade.objects.filter(
                student=enrollment.student,
                graded_work__course_task__course__grade_levels__in=[
                    enrollment.grade_level
                ],
            )
            .order_by("graded_work__course_task__course")
            .select_related(
                "graded_work__course_task", "graded_work__course_task__course"
            )
        )
        return context


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
        context["resources"] = CourseResource.objects.filter(
            course__grade_levels__in=[enrollment.grade_level]
        ).select_related("course")
        return context
