from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from homeschool.schools.models import SchoolYear

from .forms import CourseForm, CourseTaskForm
from .models import Course, CourseTask


class CourseListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        user = self.request.user
        today = user.get_local_today()
        school_year = SchoolYear.objects.filter(
            school=user.school, start_date__lte=today, end_date__gte=today
        ).first()
        return (
            Course.objects.filter(grade_level__school_year=school_year)
            .order_by("grade_level")
            .select_related("grade_level")
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        courses_by_grade_level = {}
        for course in context["object_list"]:
            if course.grade_level not in courses_by_grade_level:
                courses_by_grade_level[course.grade_level] = []
            courses_by_grade_level[course.grade_level].append(course)
        context["courses_by_grade_level"] = courses_by_grade_level

        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return (
            Course.objects.filter(grade_level__school_year__school__admin=user)
            .select_related("grade_level")
            .prefetch_related("course_tasks__graded_work")
        )


class CourseEditView(LoginRequiredMixin, UpdateView):
    form_class = CourseForm
    template_name = "courses/course_edit.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(
            grade_level__school_year__school__admin=user
        ).select_related("grade_level")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        course = kwargs["instance"]
        kwargs["initial"].update(
            {
                "monday": course.runs_on(Course.MONDAY),
                "tuesday": course.runs_on(Course.TUESDAY),
                "wednesday": course.runs_on(Course.WEDNESDAY),
                "thursday": course.runs_on(Course.THURSDAY),
                "friday": course.runs_on(Course.FRIDAY),
                "saturday": course.runs_on(Course.SATURDAY),
                "sunday": course.runs_on(Course.SUNDAY),
            }
        )
        return kwargs

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"uuid": self.kwargs["uuid"]})


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
