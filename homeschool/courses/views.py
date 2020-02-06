from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic.edit import UpdateView

from .models import CourseTask


class CourseTaskUpdateView(LoginRequiredMixin, UpdateView):
    fields = ["description", "duration"]
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return CourseTask.objects.filter(
            course__grade_level__school_year__school__admin=user
        )

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("courses:course_task_edit", kwargs={"uuid": self.object.uuid})
