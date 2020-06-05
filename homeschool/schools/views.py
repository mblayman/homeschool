from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from .forms import GradeLevelForm, SchoolYearForm
from .models import SchoolYear


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
        return reverse("schools:school_year_list")

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
            "grade_levels", "grade_levels__courses"
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
