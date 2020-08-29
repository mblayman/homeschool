from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from homeschool.schools.exceptions import NoSchoolYearError
from homeschool.schools.models import GradeLevel, SchoolYear

from .forms import CourseForm, CourseResourceForm, CourseTaskForm
from .models import Course, CourseResource, CourseTask


class CourseMixin:
    """Get a course from the uuid URL arg."""

    if TYPE_CHECKING:  # pragma: no cover
        kwargs: dict = {}
        request = HttpRequest()

    @cached_property
    def course(self):
        course_uuid = self.kwargs["uuid"]
        grade_levels = GradeLevel.objects.filter(
            school_year__school__admin=self.request.user
        )
        return get_object_or_404(
            Course.objects.filter(grade_levels__in=grade_levels).distinct(),
            uuid=course_uuid,
        )


def get_course(user, uuid):
    """Get the course if the user has access.

    This is equivalent to the mixin and exists for use with the function-based view.
    """
    grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
    return get_object_or_404(
        Course.objects.filter(grade_levels__in=grade_levels).distinct(), uuid=uuid
    )


class CourseCreateView(LoginRequiredMixin, CreateView):
    template_name = "courses/course_form.html"
    form_class = CourseForm
    initial = {
        "monday": True,
        "tuesday": True,
        "wednesday": True,
        "thursday": True,
        "friday": True,
    }

    def dispatch(self, *args, **kwargs):
        try:
            return super().dispatch(*args, **kwargs)
        except NoSchoolYearError:
            return HttpResponseRedirect(reverse("schools:school_year_list"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True

        grade_level_uuid = self.request.GET.get("grade_level")
        if grade_level_uuid:
            try:
                context["grade_level"] = GradeLevel.objects.filter(
                    school_year__school__admin=self.request.user, uuid=grade_level_uuid
                ).first()
            except ValidationError:
                # Bogus uuid. Let it slide.
                context["grade_level"] = None

        return context

    def get_success_url(self):
        return reverse("courses:detail", args=[self.object.uuid])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        school_year_uuid = self.request.GET.get("school_year")

        school_year = None
        if school_year_uuid:
            try:
                school_year = SchoolYear.objects.filter(
                    school__admin=self.request.user, uuid=school_year_uuid
                ).first()
            except ValidationError:
                # Bogus uuid. Let it slide.
                pass

        if not school_year:
            school_year = SchoolYear.get_current_year_for(self.request.user)

        if not school_year:
            raise NoSchoolYearError()

        kwargs["school_year"] = school_year
        return kwargs


class CourseDetailView(LoginRequiredMixin, DetailView):
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return (
            Course.objects.filter(grade_levels__in=grade_levels)
            .prefetch_related(
                "resources", "course_tasks__grade_level", "course_tasks__graded_work"
            )
            .distinct()
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        grade_levels = (
            self.object.grade_levels.all().order_by("id").select_related("school_year")
        )
        context["grade_levels"] = grade_levels
        if grade_levels:
            context["school_year"] = grade_levels[0].school_year
        return context


class CourseEditView(LoginRequiredMixin, UpdateView):
    form_class = CourseForm
    template_name = "courses/course_form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return Course.objects.filter(grade_levels__in=grade_levels).distinct()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # The Course queryset should protect against this ever being an index error.
        grade_level = self.object.grade_levels.all().select_related("school_year")[0]
        kwargs["school_year"] = grade_level.school_year
        return kwargs

    def get_initial(self):
        return {
            "sunday": self.object.runs_on(Course.SUNDAY),
            "monday": self.object.runs_on(Course.MONDAY),
            "tuesday": self.object.runs_on(Course.TUESDAY),
            "wednesday": self.object.runs_on(Course.WEDNESDAY),
            "thursday": self.object.runs_on(Course.THURSDAY),
            "friday": self.object.runs_on(Course.FRIDAY),
            "saturday": self.object.runs_on(Course.SATURDAY),
        }

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"uuid": self.kwargs["uuid"]})


class CourseTaskCreateView(LoginRequiredMixin, CourseMixin, CreateView):
    form_class = CourseTaskForm
    template_name = "courses/coursetask_form.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["create"] = True

        context["course"] = self.course
        grade_level = self.course.grade_levels.first()
        context["grade_levels"] = GradeLevel.objects.filter(
            school_year=grade_level.school_year_id
        )
        return context

    def get_initial(self):
        return {"duration": self.course.default_task_duration}

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("courses:detail", kwargs={"uuid": self.kwargs["uuid"]})

    def form_valid(self, form):
        response = super().form_valid(form)
        previous_task = CourseTask.get_by_uuid(
            self.request.user, self.request.GET.get("previous_task", "")
        )
        if previous_task:
            self.object.below(previous_task)
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


@login_required
def bulk_create_course_tasks(request, uuid):
    """Bulk create course tasks.

    This is using a function-based view because the CBV beat me into submission.
    For some reason, the function view worked where the CBV did not.
    """
    course = get_course(request.user, uuid)

    CourseTaskFormSet = modelformset_factory(CourseTask, form=CourseTaskForm, extra=10)
    form_kwargs = {
        "user": request.user,
        "initial": {"duration": course.default_task_duration},
    }
    if request.method == "POST":
        formset = CourseTaskFormSet(
            request.POST, form_kwargs=form_kwargs, queryset=CourseTask.objects.none()
        )
        if formset.is_valid():
            previous_task = CourseTask.get_by_uuid(
                request.user, request.GET.get("previous_task", "")
            )
            for form in formset:
                task = form.save()
                if previous_task:
                    task.below(previous_task)
                    previous_task = task

            url = reverse("courses:detail", kwargs={"uuid": uuid})
            next_url = request.GET.get("next")
            if next_url:
                url = next_url
            return HttpResponseRedirect(url)
    else:
        formset = CourseTaskFormSet(
            form_kwargs=form_kwargs, queryset=CourseTask.objects.none()
        )

    grade_level = course.grade_levels.first()
    context = {
        "course": course,
        "formset": formset,
        "grade_levels": GradeLevel.objects.filter(
            school_year=grade_level.school_year_id
        ),
    }
    return render(request, "courses/coursetask_form_bulk.html", context)


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
        context["course"] = self.object.course
        grade_level = self.object.course.grade_levels.first()
        context["grade_levels"] = GradeLevel.objects.filter(
            school_year=grade_level.school_year_id
        )
        return context

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("courses:task_edit", kwargs={"uuid": self.object.uuid})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


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


class CourseResourceCreateView(LoginRequiredMixin, CourseMixin, CreateView):
    form_class = CourseResourceForm
    template_name = "courses/courseresource_form.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["create"] = True
        context["course"] = self.course
        return context

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"uuid": self.kwargs["uuid"]})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class CourseResourceUpdateView(LoginRequiredMixin, UpdateView):
    form_class = CourseResourceForm
    template_name = "courses/courseresource_form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return (
            CourseResource.objects.filter(course__grade_levels__in=grade_levels)
            .select_related("course")
            .distinct()
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["create"] = False
        context["course"] = self.object.course
        return context

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"uuid": self.object.course.uuid})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class CourseResourceDeleteView(LoginRequiredMixin, DeleteView):
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        user = self.request.user
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return (
            CourseResource.objects.filter(course__grade_levels__in=grade_levels)
            .select_related("course")
            .distinct()
        )

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"uuid": self.object.course.uuid})
