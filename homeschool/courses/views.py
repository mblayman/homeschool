from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import CourseTaskForm
from .models import Course, CourseTask


class CourseDetailView(LoginRequiredMixin, DetailView):
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(
            grade_level__school_year__school__admin=user
        ).select_related("grade_level")


class CourseTaskCreateView(LoginRequiredMixin, CreateView):
    form_class = CourseTaskForm
    template_name = "courses/coursetask_form.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["create"] = True

        course_uuid = self.kwargs["uuid"]
        course = get_object_or_404(
            Course.objects.filter(
                grade_level__school_year__school__admin=self.request.user
            ),
            uuid=course_uuid,
        )
        context["course"] = course
        return context

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("courses:detail", kwargs={"uuid": self.kwargs["uuid"]})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.GET.get("previous_task"):
            task = CourseTask.objects.filter(
                course__grade_level__school_year__school__admin=self.request.user,
                uuid=self.request.GET.get("previous_task"),
            ).first()
            if task:
                self.object.below(task)
        return response


class CourseTaskUpdateView(LoginRequiredMixin, UpdateView):
    form_class = CourseTaskForm
    template_name = "courses/coursetask_form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return CourseTask.objects.filter(
            course__grade_level__school_year__school__admin=user
        ).select_related("course")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["course"] = self.object.course
        return context

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("courses:task_edit", kwargs={"uuid": self.object.uuid})


class CourseTaskDeleteView(LoginRequiredMixin, DeleteView):
    slug_field = "uuid"
    slug_url_kwarg = "task_uuid"

    def get_queryset(self):
        user = self.request.user
        return CourseTask.objects.filter(
            course__grade_level__school_year__school__admin=user
        )

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"uuid": self.kwargs["uuid"]})
