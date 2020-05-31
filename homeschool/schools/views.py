from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, View

from .forms import GradeLevelForm, SchoolYearForm
from .models import SchoolYear


class CurrentSchoolYearView(LoginRequiredMixin, View):
    """Show the most relevant current school year.

    That may be an in-progress school year or a future school year
    if the user is in a planning phase.
    """

    def get(self, request, *args, **kwargs):
        user = self.request.user
        today = user.get_local_today()
        school_year = SchoolYear.objects.filter(
            school__admin=user, start_date__lte=today, end_date__gte=today
        ).first()

        # Look for a future school year if there is no current one.
        # This is for new users who may be building their school year
        # for the first time.
        if not school_year:
            school_year = SchoolYear.objects.filter(
                school__admin=user, start_date__gt=today
            ).first()

        # When there is still no school year, send them to the list page
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
