from denied.authorizers import any_authorized
from denied.decorators import authorize
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render, resolve_url
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    TemplateView,
    UpdateView,
)
from django_htmx.http import HttpResponseClientRedirect

from homeschool.schools import constants as schools_constants
from homeschool.schools.exceptions import NoSchoolYearError
from homeschool.schools.forecaster import Forecaster
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.students.models import Coursework, Enrollment, Grade

from .authorizers import course_authorized, resource_authorized, task_authorized
from .forms import (
    CourseForm,
    CourseResourceForm,
    CourseTaskBulkDeleteForm,
    CourseTaskForm,
)
from .models import Course, CourseResource, CourseTask


def get_course_task_queryset(user):
    """Get a task queryset for the user."""
    grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
    return (
        CourseTask.objects.filter(course__grade_levels__in=grade_levels)
        .select_related("course")
        .distinct()
    )


class CourseCreateView(CreateView):
    template_name = "courses/course_form.html"
    form_class = CourseForm
    initial = {
        "monday": True,
        "tuesday": True,
        "wednesday": True,
        "thursday": True,
        "friday": True,
    }

    @method_decorator(authorize(any_authorized))
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
        return reverse("courses:detail", args=[self.object.id])  # type: ignore  # Issue 762

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        school_year_id = self.request.GET.get("school_year")

        school_year = None
        if school_year_id:
            school_year = SchoolYear.objects.filter(  # type: ignore  # Issue 762
                school__admin=self.request.user, id=school_year_id
            ).first()

        if not school_year:
            school_year = SchoolYear.get_current_year_for(self.request.user)  # type: ignore  # Issue 762 # noqa

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
            messages.error(self.request, "Sorry, you can’t copy that course.")
            return {}

        return {
            "name": course_to_copy.name,
            "default_task_duration": course_to_copy.default_task_duration,
        }

    @cached_property
    def course_to_copy(self) -> Course | None:
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


@method_decorator(authorize(course_authorized), "dispatch")
class CourseDetailView(DetailView):
    queryset = Course.objects.all().prefetch_related(
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

        show_completed_tasks = bool(self.request.GET.get("completed_tasks"))
        context.update(
            get_course_tasks_context(
                self.object, course_tasks, enrollments, show_completed_tasks
            )
        )

        return context


def get_course_tasks_context(course, course_tasks, enrollments, show_completed_tasks):
    """Get the context required to render the course tasks.

    This context is also required by the htmx delete view.
    """
    students = [enrollment.student for enrollment in enrollments]
    coursework: dict = {student.id: {} for student in students}
    for work in Coursework.objects.filter(
        student__in=students, course_task__course=course
    ):
        coursework[work.student_id][work.course_task_id] = work  # type: ignore  # Issue 762

    grades: dict = {student.id: {} for student in students}
    for grade in Grade.objects.filter(
        student__in=students, graded_work__course_task__course=course
    ).select_related("graded_work__course_task"):
        grades[grade.student_id][grade.graded_work.course_task_id] = grade  # type: ignore  # Issue 762 # noqa

    grade_levels_by_student = {
        enrollment.student: enrollment.grade_level_id for enrollment in enrollments
    }

    forecasts = _get_forecasts(students, course)

    task_details = []
    for number, task in enumerate(course_tasks, start=1):
        task_detail = {
            "number": number,
            "task": task,
            "student_details": [],
            "complete": bool(students),
        }
        for enrollment in enrollments:
            student = enrollment.student
            assigned = (
                not task.grade_level_id
                or task.grade_level_id == grade_levels_by_student[student]
            )
            work = coursework[student.id].get(task.id)
            student_detail = {
                "student": student,
                "coursework": work,
                "grade": grades[student.id].get(task.id),
                "assigned": assigned,
                "planned_date": forecasts[student].get(task, {}).get("planned_date"),
            }
            task_detail["student_details"].append(student_detail)

            # Only check grade level specific tasks when the student is in the grade.
            if (
                task.grade_level_id is None
                or task.grade_level_id == enrollment.grade_level_id
            ) and not work:
                task_detail["complete"] = False

        if not students:
            task_detail["planned_date"] = (
                forecasts[None].get(task, {}).get("planned_date")
            )

        if task_detail["complete"] and not show_completed_tasks:
            continue

        task_details.append(task_detail)
    return {"task_details": task_details}


def _get_forecasts(students, course):
    """Get the forecast dates for all the students.

    If there are no students, a generic forecast is added to the None key.
    """
    forecaster = Forecaster()
    forecasts = {}
    for student in students:
        forecasts[student] = forecaster.get_items_by_task(student, course)

    if not students:
        forecasts[None] = forecaster.get_items_by_task(student=None, course=course)

    return forecasts


@method_decorator(authorize(course_authorized), "dispatch")
class CourseEditView(UpdateView):
    form_class = CourseForm
    template_name = "courses/course_form.html"
    queryset = Course.objects.all()

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


@method_decorator(authorize(course_authorized), "dispatch")
class CourseDeleteView(DeleteView):
    queryset = Course.objects.all()

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


@method_decorator(authorize(any_authorized), "dispatch")
class CourseCopySelectView(TemplateView):
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


@method_decorator(authorize(course_authorized), "dispatch")
class CourseTaskCreateView(CreateView):
    form_class = CourseTaskForm
    template_name = "courses/coursetask_form.html"

    @cached_property
    def course(self):
        return Course.objects.get(pk=self.kwargs["pk"])

    @cached_property
    def previous_task(self):
        return CourseTask.get_by_id(
            self.request.user, self.request.GET.get("previous_task", "")  # type: ignore  # Issue 762 # noqa
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["create"] = True

        context["course"] = self.course
        context["grade_levels"] = self.course.grade_levels.all()
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
            self.object.below(self.previous_task)  # type: ignore  # Issue 762
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

        original_description = self.object.description  # type: ignore  # Issue 762

        autonumber = self.request.POST.get("autonumber")
        if autonumber:
            try:
                starting_at = int(self.request.POST.get("starting_at", 1))
            except ValueError:
                # Bad POST data. Stop.
                return

            self.object.description = f"{original_description} {starting_at}"  # type: ignore  # Issue 762 # noqa
            self.object.save()  # type: ignore  # Issue 762
        else:
            starting_at = 1

        previous_task = self.object
        # A copy of the POST is needed for mutable access for autonumber to work.
        data = self.request.POST.copy()
        # The first autonumber is handled separately so bump the starting counter.
        starting_at += 1
        for autonumber_counter, _ in enumerate(
            range(replicate_count), start=starting_at
        ):
            if autonumber:
                data["description"] = f"{original_description} {autonumber_counter}"

            form = CourseTaskForm(user=self.request.user, data=data)
            # This method should only be called after the first form was validated.
            # That should make this is_valid call safe and populate cleaned_data.
            form.is_valid()
            form.save()
            form.instance.below(previous_task)
            previous_task = form.instance


@authorize(course_authorized)
def bulk_create_course_tasks(request, pk):
    """Bulk create course tasks.

    This is using a function-based view because the CBV beat me into submission.
    For some reason, the function view worked where the CBV did not.
    """
    course = Course.objects.get(pk=pk)
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


@authorize(course_authorized)
def get_course_task_bulk_hx(request, pk, last_form_number):
    """Get the next set of empty forms to display for bulk edit.

    This returns an HTML fragment of forms for htmx.
    """
    course = Course.objects.get(pk=pk)
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
        "forms": formset[-form_count:],  # type: ignore  # Issue 762
        "last_form_number": last_form_number,
    }
    return render(request, "courses/coursetask_form_bulk_partial.html", context)


@method_decorator(authorize(task_authorized), "dispatch")
class CourseTaskUpdateView(UpdateView):
    form_class = CourseTaskForm
    template_name = "courses/coursetask_form.html"
    queryset = CourseTask.objects.all().select_related("course")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["course"] = self.object.course
        context["grade_levels"] = self.object.course.grade_levels.all()
        context["previous_task"] = self.object.previous()
        context["delete_url"] = self._get_delete_url()
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

    def _get_delete_url(self):
        """Get the delete URL.

        Adjust the task fragment to point to the previous task.
        """
        delete_url = resolve_url(
            "courses:task_delete", course_id=self.object.course_id, pk=self.object.pk
        )
        if "next" in self.request.GET:
            next_url = self.request.GET["next"]

            # Some part of the URL may have the current task *outside*
            # of the URL fragment. Thus, we use our knowledge of the fragment name,
            # and include that prefix to ensure a single replacement.
            previous_task = self.object.previous()
            if previous_task:
                next_url = next_url.replace(
                    f"task-{self.object.id}", f"task-{previous_task.id}"
                )

            delete_url += f"?next={next_url}"
        return delete_url


@authorize(course_authorized)
def bulk_delete_course_tasks(request, pk):
    """Bulk delete course tasks."""
    course = Course.objects.get(pk=pk)
    tasks = get_course_task_queryset(request.user).filter(course=course)

    if request.method == "POST":
        form = CourseTaskBulkDeleteForm(request.POST, user=request.user)
        if form.is_valid():
            deleted_tasks_count = form.save()
            messages.info(request, f"Deleted {deleted_tasks_count} tasks.")
            url = reverse("courses:detail", args=[course.id])
            return HttpResponseClientRedirect(url)

        error_message = form.non_field_errors()[0]
        messages.error(request, error_message)
        url = reverse("courses:task_delete_bulk", args=[course.id])
        return HttpResponseClientRedirect(url)

    show_completed_tasks = bool(request.GET.get("completed_tasks"))
    grade_levels = course.grade_levels.all().order_by("id")
    enrollments = [
        enrollment
        for enrollment in Enrollment.objects.filter(grade_level__in=grade_levels)
        .select_related("student")
        .order_by("grade_level")
    ]

    context = {
        "course": course,
        "course_tasks": tasks,
        "enrolled_students": [enrollment.student for enrollment in enrollments],
    }
    context.update(
        get_course_tasks_context(course, tasks, enrollments, show_completed_tasks)
    )
    return render(request, "courses/coursetask_bulk_delete.html", context)


@method_decorator(authorize(task_authorized), "dispatch")
class CourseTaskDeleteView(DeleteView):
    queryset = CourseTask.objects.all().select_related("course")

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("courses:detail", kwargs={"pk": self.kwargs["course_id"]})


@authorize(task_authorized)
@require_http_methods(["DELETE"])
def course_task_hx_delete(request, pk):
    """Delete a course task via htmx."""
    task = CourseTask.objects.select_related("course").get(pk=pk)
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

    show_completed_tasks = bool(request.GET.get("completed_tasks"))
    grade_levels = task.course.grade_levels.all().order_by("id")
    enrollments = [
        enrollment
        for enrollment in Enrollment.objects.filter(grade_level__in=grade_levels)
        .select_related("student")
        .order_by("grade_level")
    ]
    context.update(
        get_course_tasks_context(
            course, course_tasks, enrollments, show_completed_tasks
        )
    )

    return render(request, "courses/course_tasks.html", context)


@require_POST
@authorize(task_authorized)
def move_task_down(request, pk):
    """Move a task down in the ordering."""
    task = CourseTask.objects.get(pk=pk)
    task.down()
    url = reverse("courses:detail", args=[task.course_id])
    url += f"#task-{task.id}"
    return HttpResponseRedirect(url)


@require_POST
@authorize(task_authorized)
def move_task_up(request, pk):
    """Move a task up in the ordering."""
    task = CourseTask.objects.get(pk=pk)
    task.up()
    url = reverse("courses:detail", args=[task.course_id])
    url += f"#task-{task.id}"
    return HttpResponseRedirect(url)


@method_decorator(authorize(course_authorized), "dispatch")
class CourseResourceCreateView(CreateView):
    form_class = CourseResourceForm
    template_name = "courses/courseresource_form.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["create"] = True
        context["course"] = Course.objects.get(pk=self.kwargs["pk"])
        return context

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"pk": self.kwargs["pk"]})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(authorize(resource_authorized), "dispatch")
class CourseResourceUpdateView(UpdateView):
    form_class = CourseResourceForm
    template_name = "courses/courseresource_form.html"
    queryset = CourseResource.objects.all().select_related("course")

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


@method_decorator(authorize(resource_authorized), "dispatch")
class CourseResourceDeleteView(DeleteView):
    queryset = CourseResource.objects.all().select_related("course")

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"pk": self.object.course.id})
