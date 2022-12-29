from denied.authorizers import any_authorized
from denied.decorators import authorize
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from homeschool.students.models import Enrollment

from .authorizers import (
    grade_level_authorized,
    school_break_authorized,
    school_year_authorized,
)
from .forecaster import Forecaster
from .forms import GradeLevelForm, SchoolBreakForm, SchoolYearForm
from .models import GradeLevel, SchoolBreak, SchoolYear
from .year_calendar import YearCalendar


@authorize(any_authorized)
def current_school_year(request):
    """Show the most relevant current school year.

    That may be an in-progress school year or a future school year
    if the user is in a planning phase.
    """
    school_year = SchoolYear.get_current_year_for(request.user)

    # When there is no school year, send them to the list page
    # so the user can see where to create a new school year.
    if not school_year:
        return HttpResponseRedirect(reverse("schools:school_year_list"))

    return SchoolYearDetailView.as_view()(request, pk=school_year.id)


@method_decorator(authorize(any_authorized), "dispatch")
class SchoolYearCreateView(CreateView):
    template_name = "schools/schoolyear_form.html"
    form_class = SchoolYearForm
    initial = {
        "monday": True,
        "tuesday": True,
        "wednesday": True,
        "thursday": True,
        "friday": True,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        return context

    def get_success_url(self):
        # A create view will definitely have an object
        # by the time the success url is needed. Ignore type check.
        return reverse("schools:school_year_detail", args=[self.object.id])  # type: ignore

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(authorize(school_year_authorized), "dispatch")
class SchoolYearDetailView(DetailView):
    queryset = SchoolYear.objects.all().prefetch_related("breaks", "grade_levels")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_link"] = "school_year"

        today = self.request.user.get_local_today()  # type: ignore  # Issue 762
        context["calendar"] = YearCalendar(self.object, today).build(
            show_all=bool(self.request.GET.get("show_all_months"))
        )
        context["is_in_school_year"] = self.object.contains(today)
        context["grade_levels"] = []
        for grade_level in self.object.grade_levels.all():
            context["grade_levels"].append(
                {
                    "grade_level": grade_level,
                    "courses": grade_level.get_ordered_courses(),
                    "has_students": Enrollment.objects.filter(
                        grade_level=grade_level
                    ).exists(),
                }
            )
        return context


@method_decorator(authorize(school_year_authorized), "dispatch")
class SchoolYearEditView(UpdateView):
    form_class = SchoolYearForm
    template_name = "schools/schoolyear_form.html"
    queryset = SchoolYear.objects.all()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        return {
            "sunday": self.object.runs_on(SchoolYear.SUNDAY),
            "monday": self.object.runs_on(SchoolYear.MONDAY),
            "tuesday": self.object.runs_on(SchoolYear.TUESDAY),
            "wednesday": self.object.runs_on(SchoolYear.WEDNESDAY),
            "thursday": self.object.runs_on(SchoolYear.THURSDAY),
            "friday": self.object.runs_on(SchoolYear.FRIDAY),
            "saturday": self.object.runs_on(SchoolYear.SATURDAY),
        }

    def get_success_url(self):
        return reverse("schools:school_year_detail", kwargs={"pk": self.kwargs["pk"]})


def move_grade_level(user, grade_level_id, direction, next_url):
    """Move the grade level ordering in the specified direction."""
    grade_level = GradeLevel.objects.get(pk=grade_level_id)
    getattr(grade_level, direction)()

    if next_url is None:
        next_url = reverse(
            "schools:school_year_edit", args=[grade_level.school_year_id]
        )
    return HttpResponseRedirect(next_url)


@require_POST
@authorize(grade_level_authorized)
def move_grade_level_down(request, pk):
    """Move a grade level down in the ordering."""
    return move_grade_level(request.user, pk, "down", request.GET.get("next"))


@require_POST
@authorize(grade_level_authorized)
def move_grade_level_up(request, pk):
    """Move a grade level up in the ordering."""
    return move_grade_level(request.user, pk, "up", request.GET.get("next"))


@authorize(school_year_authorized)
def school_year_forecast(request, pk):
    school_year = SchoolYear.objects.get(pk=pk)

    enrollments = Enrollment.objects.filter(
        grade_level__school_year=school_year
    ).select_related("grade_level", "student")
    students = []
    for enrollment in enrollments:
        student_info = {"student": enrollment.student, "courses": []}

        for course in enrollment.grade_level.get_ordered_courses():
            forecaster = Forecaster()
            course_info = {
                "course": course,
                "last_forecast_date": forecaster.get_last_forecast_date(
                    enrollment.student, course
                ),
            }
            student_info["courses"].append(course_info)

        students.append(student_info)

    context = {
        "schoolyear": school_year,
        "show_empty": not any(student_info["courses"] for student_info in students),
        "students": students,
    }
    return render(request, "schools/schoolyear_forecast.html", context)


@method_decorator(authorize(any_authorized), "dispatch")
class SchoolYearListView(ListView):
    def get_queryset(self):
        user = self.request.user
        return SchoolYear.objects.filter(school__admin=user).order_by("-start_date")  # type: ignore  # Issue 762 # noqa

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_link"] = "school_year"
        return context


@method_decorator(authorize(school_year_authorized), "dispatch")
class GradeLevelCreateView(CreateView):
    form_class = GradeLevelForm
    template_name = "schools/gradelevel_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["school_year"] = SchoolYear.objects.get(pk=self.kwargs["pk"])
        return context

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.kwargs["pk"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(authorize(grade_level_authorized), "dispatch")
class GradeLevelDetailView(DetailView):
    queryset = GradeLevel.objects.all().select_related("school_year")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_year = self.object.school_year
        context["school_year"] = school_year
        context["enrollments"] = self.object.enrollments.select_related("student").all()
        context["show_enroll_cta"] = Enrollment.has_unenrolled_students(school_year)
        return context


@method_decorator(authorize(grade_level_authorized), "dispatch")
class GradeLevelUpdateView(UpdateView):
    form_class = GradeLevelForm
    template_name = "schools/gradelevel_form.html"
    queryset = GradeLevel.objects.all().select_related("school_year")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["school_year"] = self.object.school_year
        return context

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.object.school_year.id])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


def move_course(user, grade_level_id, course_id, direction, next_url):
    """Move the course ordering in the specified direction."""
    grade_level = GradeLevel.objects.get(pk=grade_level_id)
    course = grade_level.courses.get(id=course_id)
    getattr(grade_level, direction)(course)

    if next_url is None:
        next_url = reverse("schools:grade_level_edit", args=[grade_level_id])
    return HttpResponseRedirect(next_url)


@require_POST
@authorize(grade_level_authorized)
def move_course_down(request, pk, course_id):
    """Move a course down in the ordering."""
    return move_course(
        request.user, pk, course_id, "move_course_down", request.GET.get("next")
    )


@require_POST
@authorize(grade_level_authorized)
def move_course_up(request, pk, course_id):
    """Move a course up in the ordering."""
    return move_course(
        request.user, pk, course_id, "move_course_up", request.GET.get("next")
    )


@method_decorator(authorize(school_year_authorized), "dispatch")
class SchoolBreakCreateView(CreateView):
    form_class = SchoolBreakForm
    template_name = "schools/schoolbreak_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        school_year = SchoolYear.objects.get(pk=self.kwargs["pk"])
        context["school_year"] = school_year
        context["students"] = Enrollment.get_students_for_school_year(school_year)
        return context

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.kwargs["pk"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(authorize(school_break_authorized), "dispatch")
class SchoolBreakUpdateView(UpdateView):
    form_class = SchoolBreakForm
    template_name = "schools/schoolbreak_form.html"
    queryset = SchoolBreak.objects.all().select_related("school_year")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["school_year"] = self.object.school_year
        students = Enrollment.get_students_for_school_year(self.object.school_year)

        students_on_break = self.object.students.all()
        for student in students:
            student.is_on_break = not bool(
                students_on_break and student not in students_on_break
            )

        context["students"] = students
        return context

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.object.school_year.id])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(authorize(school_break_authorized), "dispatch")
class SchoolBreakDeleteView(DeleteView):
    queryset = SchoolBreak.objects.all().select_related("school_year")

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.object.school_year.id])
