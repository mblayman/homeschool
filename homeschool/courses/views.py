from typing import TYPE_CHECKING, Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    TemplateView,
    UpdateView,
)
from waffle import flag_is_active

from homeschool.schools import constants as schools_constants
from homeschool.schools.exceptions import NoSchoolYearError
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.students.models import Coursework, Enrollment, Grade

from .forms import CourseForm, CourseResourceForm, CourseTaskForm
from .models import Course, CourseResource, CourseTask


class CourseMixin:
    """Get a course from the pk URL arg."""

    if TYPE_CHECKING:  # pragma: no cover
        kwargs: dict = {}
        request = HttpRequest()

    @cached_property
    def course(self):
        course_id = self.kwargs["pk"]
        grade_levels = GradeLevel.objects.filter(
            school_year__school__admin=self.request.user
        )
        return get_object_or_404(
            Course.objects.filter(grade_levels__in=grade_levels).distinct(),
            id=course_id,
        )


def get_course(user, pk):
    """Get the course if the user has access.

    This is equivalent to the mixin and exists for use with the function-based view.
    """
    grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
    return get_object_or_404(
        Course.objects.filter(grade_levels__in=grade_levels).distinct(), pk=pk
    )


def get_course_task_queryset(user):
    """Get a task queryset for the user."""
    grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
    return (
        CourseTask.objects.filter(course__grade_levels__in=grade_levels)
        .select_related("course")
        .distinct()
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

        grade_level_id = self.request.GET.get("grade_level")
        if grade_level_id:
            context["grade_level"] = GradeLevel.objects.filter(
                school_year__school__admin=self.request.user, id=grade_level_id
            ).first()

        context["course_to_copy"] = self.course_to_copy
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        if self.course_to_copy:
            self.course_to_copy.copy_to(self.object)

        return response

    def get_success_url(self):
        return reverse("courses:detail", args=[self.object.id])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        school_year_id = self.request.GET.get("school_year")

        school_year = None
        if school_year_id:
            school_year = SchoolYear.objects.filter(
                school__admin=self.request.user, id=school_year_id
            ).first()

        if not school_year:
            school_year = SchoolYear.get_current_year_for(self.request.user)

        if not school_year:
            raise NoSchoolYearError()

        kwargs["school_year"] = school_year
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial.update(self.get_copied_course_info())
        return initial

    def get_copied_course_info(self):
        """When the user wants to copy the course, prepopulate the form."""
        if "copy_from" not in self.request.GET:
            return {}

        course_to_copy = self.course_to_copy
        if course_to_copy is None:
            messages.add_message(
                self.request, messages.ERROR, "Sorry, you can’t copy that course."
            )
            return {}

        return {
            "name": course_to_copy.name,
            "default_task_duration": course_to_copy.default_task_duration,
        }

    @cached_property
    def course_to_copy(self) -> Optional[Course]:
        """Get the course to copy if the query arg is present."""
        if "copy_from" not in self.request.GET:
            return None

        user = self.request.user
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        try:
            return Course.objects.distinct().get(
                grade_levels__in=grade_levels, id=self.request.GET["copy_from"]
            )
        except (Course.DoesNotExist, ValidationError):
            pass
        return None


class CourseQuerySetMixin:
    if TYPE_CHECKING:  # pragma: no cover
        request = HttpRequest()

    def get_course_queryset(self):
        user = self.request.user
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return Course.objects.filter(grade_levels__in=grade_levels).distinct()


class CourseDetailView(LoginRequiredMixin, CourseQuerySetMixin, DetailView):
    def get_queryset(self):
        course_qs = self.get_course_queryset()
        return course_qs.prefetch_related(
            "resources", "course_tasks__grade_level", "course_tasks__graded_work"
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        grade_levels = (
            self.object.grade_levels.all().order_by("id").select_related("school_year")
        )
        context["grade_levels"] = grade_levels

        enrollments = []
        students = []
        if grade_levels:
            context["school_year"] = grade_levels[0].school_year
            enrollments = [
                enrollment
                for enrollment in Enrollment.objects.filter(
                    grade_level__in=grade_levels
                )
                .select_related("student")
                .order_by("grade_level")
            ]
            students = [enrollment.student for enrollment in enrollments]
        context["enrolled_students"] = students

        course_tasks = list(self.object.course_tasks.all())
        context["course_tasks"] = course_tasks

        last_task = None
        if course_tasks:
            last_task = course_tasks[-1]
        context["last_task"] = last_task

        if flag_is_active(self.request, "combined_course_flag"):
            context.update(
                get_course_tasks_context(self.object, course_tasks, enrollments)
            )

        return context


def get_course_tasks_context(course, course_tasks, enrollments):
    """Get the context required to render the course tasks.

    This context is also required by the htmx delete view.
    """
    students = [enrollment.student for enrollment in enrollments]
    coursework: dict = {student.id: {} for student in students}
    for work in Coursework.objects.filter(
        student__in=students, course_task__course=course
    ):
        coursework[work.student_id][work.course_task_id] = work

    grades: dict = {student.id: {} for student in students}
    for grade in Grade.objects.filter(
        student__in=students, graded_work__course_task__course=course
    ).select_related("graded_work__course_task"):
        grades[grade.student_id][grade.graded_work.course_task_id] = grade

    grade_levels_by_student = {
        enrollment.student: enrollment.grade_level_id for enrollment in enrollments
    }

    task_details = []
    for task in course_tasks:
        task_detail = {"task": task, "student_details": []}
        for student in students:
            assigned = (
                not task.grade_level_id
                or task.grade_level_id == grade_levels_by_student[student]
            )
            student_detail = {
                "student": student,
                "coursework": coursework[student.id].get(task.id),
                "grade": grades[student.id].get(task.id),
                "assigned": assigned,
            }
            task_detail["student_details"].append(student_detail)
        task_details.append(task_detail)
    return {"task_details": task_details}


class CourseEditView(LoginRequiredMixin, CourseQuerySetMixin, UpdateView):
    form_class = CourseForm
    template_name = "courses/course_form.html"

    def get_queryset(self):
        return self.get_course_queryset()

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
        return reverse("courses:detail", kwargs={"pk": self.kwargs["pk"]})


class CourseDeleteView(LoginRequiredMixin, CourseQuerySetMixin, DeleteView):
    def get_queryset(self):
        return self.get_course_queryset()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["tasks_count"] = CourseTask.objects.filter(course=self.object).count()
        context["coursework_count"] = Coursework.objects.filter(
            course_task__course=self.object
        ).count()
        context["grades_count"] = Grade.objects.filter(
            graded_work__course_task__course=self.object
        ).count()
        context["course_resources_count"] = CourseResource.objects.filter(
            course=self.object
        ).count()
        return context

    def get_success_url(self):
        grade_level = self.object.grade_levels.select_related("school_year").first()
        return reverse(
            "schools:school_year_detail", kwargs={"pk": grade_level.school_year.id}
        )


class CourseCopySelectView(LoginRequiredMixin, TemplateView):
    """Display all courses so that the user can select one to copy."""

    template_name = "courses/copy.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user = self.request.user
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        school_years: dict = {}
        for course in (
            Course.objects.filter(grade_levels__in=grade_levels)
            .prefetch_related("grade_levels", "grade_levels__school_year")
            .distinct()
        ):
            school_year = None
            # A course will only be in one school year, but using first()
            # busts the prefetch cache so we have this silly for loop instead.
            for grade_level in course.grade_levels.all():
                school_year = grade_level.school_year
                break

            if school_year not in school_years:
                school_years[school_year] = {}
            if grade_level not in school_years[school_year]:
                school_years[school_year][grade_level] = []
            school_years[school_year][grade_level].append(course)

        context["school_years"] = [
            {"school_year": school_year, "grade_levels": grade_levels}
            for school_year, grade_levels in sorted(
                school_years.items(), key=lambda pair: pair[0].start_date
            )
        ]
        return context


class CourseTaskCreateView(LoginRequiredMixin, CourseMixin, CreateView):
    form_class = CourseTaskForm
    template_name = "courses/coursetask_form.html"

    @cached_property
    def previous_task(self):
        return CourseTask.get_by_id(
            self.request.user, self.request.GET.get("previous_task", "")
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["create"] = True

        context["course"] = self.course
        grade_level = self.course.grade_levels.first()
        context["grade_levels"] = GradeLevel.objects.filter(
            school_year=grade_level.school_year_id
        )
        context["previous_task"] = self.previous_task
        context["max_tasks"] = schools_constants.MAX_ALLOWED_DAYS
        return context

    def get_initial(self):
        return {"duration": self.course.default_task_duration}

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("courses:detail", kwargs={"pk": self.kwargs["pk"]})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.previous_task:
            self.object.below(self.previous_task)
        replicate = self.request.POST.get("replicate")
        if replicate:
            self.create_copies()
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def create_copies(self):
        """Create copies that a user requested.

        This should create 1 less than the requested amount
        because the CreateView already created the first instance.
        """
        try:
            replicate_count = int(self.request.POST.get("replicate_count", 1))
            replicate_count = min(replicate_count, schools_constants.MAX_ALLOWED_DAYS)
            replicate_count -= 1
        except ValueError:
            # Bad POST data. Stop.
            return

        original_description = self.object.description
        autonumber = self.request.POST.get("autonumber")
        if autonumber:
            self.object.description = f"{original_description} 1"
            self.object.save()

        previous_task = self.object
        # A copy of the POST is needed for mutable access for autonumber to work.
        data = self.request.POST.copy()
        for autonumber_counter, _ in enumerate(range(replicate_count), start=2):
            if autonumber:
                data["description"] = f"{original_description} {autonumber_counter}"

            form = CourseTaskForm(user=self.request.user, data=data)
            # This method should only be called after the first form was validated.
            # That should make this is_valid call safe and populate cleaned_data.
            form.is_valid()
            form.save()
            form.instance.below(previous_task)
            previous_task = form.instance


@login_required
def bulk_create_course_tasks(request, pk):
    """Bulk create course tasks.

    This is using a function-based view because the CBV beat me into submission.
    For some reason, the function view worked where the CBV did not.
    """
    course = get_course(request.user, pk)
    previous_task = CourseTask.get_by_id(
        request.user, request.GET.get("previous_task", "")
    )

    extra_forms = 3
    CourseTaskFormSet = modelformset_factory(
        CourseTask, form=CourseTaskForm, extra=extra_forms
    )
    form_kwargs = {
        "user": request.user,
        "initial": {"duration": course.default_task_duration},
    }
    if request.method == "POST":
        formset = CourseTaskFormSet(
            request.POST, form_kwargs=form_kwargs, queryset=CourseTask.objects.none()
        )
        if formset.is_valid():
            for form in formset:
                task = form.save()
                if previous_task:
                    task.below(previous_task)
                    previous_task = task

            url = reverse("courses:detail", kwargs={"pk": pk})
            next_url = request.GET.get("next")
            if next_url:
                url = next_url
            return HttpResponseRedirect(url)
    else:
        formset = CourseTaskFormSet(
            form_kwargs=form_kwargs, queryset=CourseTask.objects.none()
        )

    context = {
        "course": course,
        "formset": formset,
        "grade_levels": course.grade_levels.all(),
        "previous_task": previous_task,
        # Cast to str to avoid some ugly template filters.
        "extra_forms": str(extra_forms),
    }
    return render(request, "courses/coursetask_form_bulk.html", context)


@login_required
def get_course_task_bulk_hx(request, pk, last_form_number):
    """Get the next set of empty forms to display for bulk edit.

    This returns an HTML fragment of forms for htmx.
    """
    course = get_course(request.user, pk)
    total_existing_forms = last_form_number + 1

    # Formsets won't create the latest forms so this must re-create *all* forms
    # then slice from the end to get the forms that are needed. Efficient? Heck no.
    form_count = 3
    extra_forms = total_existing_forms + form_count
    CourseTaskFormSet = modelformset_factory(
        CourseTask, form=CourseTaskForm, extra=extra_forms
    )
    formset = CourseTaskFormSet(
        form_kwargs={
            "user": request.user,
            "initial": {"duration": course.default_task_duration},
        },
        queryset=CourseTask.objects.none(),
    )

    context = {
        "course": course,
        "grade_levels": course.grade_levels.all(),
        "forms": formset[-form_count:],
        "last_form_number": last_form_number,
    }
    return render(request, "courses/coursetask_form_bulk_partial.html", context)


class CourseTaskUpdateView(LoginRequiredMixin, UpdateView):
    form_class = CourseTaskForm
    template_name = "courses/coursetask_form.html"

    def get_queryset(self):
        return get_course_task_queryset(self.request.user).select_related("course")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["course"] = self.object.course
        grade_level = self.object.course.grade_levels.first()
        context["grade_levels"] = GradeLevel.objects.filter(
            school_year=grade_level.school_year_id
        )
        context["previous_task"] = self.object.previous()
        return context

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("courses:task_edit", kwargs={"pk": self.object.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        return {"is_graded": hasattr(self.object, "graded_work")}


class CourseTaskDeleteView(LoginRequiredMixin, DeleteView):
    def get_queryset(self):
        return get_course_task_queryset(self.request.user)

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("courses:detail", kwargs={"pk": self.kwargs["course_id"]})


@login_required
@require_http_methods(["DELETE"])
def course_task_hx_delete(request, pk):
    """Delete a course task via htmx."""
    task = get_object_or_404(
        get_course_task_queryset(request.user).select_related("course"), pk=pk
    )
    course = task.course
    course_tasks = (
        task.course.course_tasks.all()
        .select_related("grade_level")
        .prefetch_related("graded_work")
    )
    context = {"course": course, "course_tasks": course_tasks}

    # Context collection evaluates before template rendering
    # so the task needs to be deleted before getting the new context.
    task.delete()

    if flag_is_active(request, "combined_course_flag"):
        grade_levels = task.course.grade_levels.all().order_by("id")
        enrollments = [
            enrollment
            for enrollment in Enrollment.objects.filter(grade_level__in=grade_levels)
            .select_related("student")
            .order_by("grade_level")
        ]
        context.update(get_course_tasks_context(course, course_tasks, enrollments))

    return render(request, "courses/course_tasks.html", context)


@login_required
@require_POST
def move_task_down(request, pk):
    """Move a task down in the ordering."""
    task = get_object_or_404(
        get_course_task_queryset(request.user).select_related("course"), pk=pk
    )
    task.down()
    url = reverse("courses:detail", args=[task.course.id])
    url += f"#task-{task.id}"
    return HttpResponseRedirect(url)


@login_required
@require_POST
def move_task_up(request, pk):
    """Move a task up in the ordering."""
    task = get_object_or_404(
        get_course_task_queryset(request.user).select_related("course"), pk=pk
    )
    task.up()
    url = reverse("courses:detail", args=[task.course.id])
    url += f"#task-{task.id}"
    return HttpResponseRedirect(url)


class CourseResourceCreateView(LoginRequiredMixin, CourseMixin, CreateView):
    form_class = CourseResourceForm
    template_name = "courses/courseresource_form.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["create"] = True
        context["course"] = self.course
        return context

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"pk": self.kwargs["pk"]})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class CourseResourceUpdateView(LoginRequiredMixin, UpdateView):
    form_class = CourseResourceForm
    template_name = "courses/courseresource_form.html"

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
        return reverse("courses:detail", kwargs={"pk": self.object.course.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class CourseResourceDeleteView(LoginRequiredMixin, DeleteView):
    def get_queryset(self):
        user = self.request.user
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return (
            CourseResource.objects.filter(course__grade_levels__in=grade_levels)
            .select_related("course")
            .distinct()
        )

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"pk": self.object.course.id})
