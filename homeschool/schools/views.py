from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView

from .models import SchoolYear


class SchoolYearDetailView(LoginRequiredMixin, DetailView):
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return SchoolYear.objects.filter(school__admin=user).prefetch_related(
            "grade_levels", "grade_levels__courses"
        )
