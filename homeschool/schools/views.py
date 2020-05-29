from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, View

from .models import SchoolYear


class CurrentSchoolYearView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = self.request.user
        today = user.get_local_today()
        school_year = SchoolYear.objects.filter(
            school__admin=user, start_date__lte=today, end_date__gte=today
        ).first()
        if not school_year:
            return HttpResponseRedirect(reverse("schools:school_year_list"))
        return SchoolYearDetailView.as_view()(request, uuid=school_year.uuid)


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
        return SchoolYear.objects.filter(school__admin=user)
