from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from homeschool.students.models import Enrollment, Grade

from .forms import GradeLevelForm, SchoolBreakForm, SchoolYearForm
from .models import SchoolBreak, SchoolYear


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
            "breaks", "grade_levels", "grade_levels__courses"
        )


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
            "monday": self.object.runs_on(SchoolYear.MONDAY),
            "tuesday": self.object.runs_on(SchoolYear.TUESDAY),
            "wednesday": self.object.runs_on(SchoolYear.WEDNESDAY),
            "thursday": self.object.runs_on(SchoolYear.THURSDAY),
            "friday": self.object.runs_on(SchoolYear.FRIDAY),
            "saturday": self.object.runs_on(SchoolYear.SATURDAY),
            "sunday": self.object.runs_on(SchoolYear.SUNDAY),
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
