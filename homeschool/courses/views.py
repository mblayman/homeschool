from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from homeschool.schools.models import GradeLevel, SchoolYear

from .forms import CourseForm, CourseTaskForm
from .models import Course, CourseTask


class CourseListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        user = self.request.user
        today = user.get_local_today()
        school_year = SchoolYear.objects.filter(
            school=user.school, start_date__lte=today, end_date__gte=today
        ).first()
        grade_levels = GradeLevel.objects.filter(school_year=school_year)
        return (
            Course.objects.filter(grade_levels__in=grade_levels)
            .order_by("grade_levels")
            .prefetch_related("grade_levels")
            .distinct()
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        courses_by_grade_level = {}
        for course in context["object_list"]:
            for grade_level in course.grade_levels.all():
                if grade_level not in courses_by_grade_level:
                    courses_by_grade_level[grade_level] = []
                if course not in courses_by_grade_level[grade_level]:
                    courses_by_grade_level[grade_level].append(course)
        context["courses_by_grade_level"] = courses_by_grade_level

        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return (
            Course.objects.filter(grade_levels__in=grade_levels)
            .prefetch_related("course_tasks__grade_level", "course_tasks__graded_work")
            .distinct()
        )


class CourseEditView(LoginRequiredMixin, UpdateView):
    form_class = CourseForm
    template_name = "courses/course_edit.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return Course.objects.filter(grade_levels__in=grade_levels).distinct()

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
        user = self.request.user

        course_uuid = self.kwargs["uuid"]
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        course = get_object_or_404(
            Course.objects.filter(grade_levels__in=grade_levels).distinct(),
            uuid=course_uuid,
        )
        context["course"] = course
        context["current_grade_levels"] = user.school.get_current_grade_levels()
        return context

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("courses:detail", kwargs={"uuid": self.kwargs["uuid"]})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.GET.get("previous_task"):
            grade_levels = GradeLevel.objects.filter(
                school_year__school__admin=self.request.user
            )
            task = CourseTask.objects.filter(
                course__grade_levels__in=grade_levels,
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
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return (
            CourseTask.objects.filter(course__grade_levels__in=grade_levels)
            .select_related("course")
            .distinct()
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user = self.request.user
        context["course"] = self.object.course
        context["current_grade_levels"] = user.school.get_current_grade_levels()
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
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return CourseTask.objects.filter(
            course__grade_levels__in=grade_levels
        ).distinct()

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"uuid": self.kwargs["uuid"]})
