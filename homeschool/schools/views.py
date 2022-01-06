from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from homeschool.students.models import Enrollment

from .forecaster import Forecaster
from .forms import GradeLevelForm, SchoolBreakForm, SchoolYearForm
from .models import GradeLevel, SchoolBreak, SchoolYear
from .year_calendar import YearCalendar


class CurrentSchoolYearView(LoginRequiredMixin, View):
    """Show the most relevant current school year.

    That may be an in-progress school year or a future school year
    if the user is in a planning phase.
    """

    def get(self, request, *args, **kwargs):
        user = self.request.user
        school_year = SchoolYear.get_current_year_for(user)

        # When there is no school year, send them to the list page
        # so the user can see where to create a new school year.
        if not school_year:
            return HttpResponseRedirect(reverse("schools:school_year_list"))

        return SchoolYearDetailView.as_view()(request, pk=school_year.id)


class SchoolYearCreateView(LoginRequiredMixin, CreateView):
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
        return reverse("schools:school_year_detail", args=[self.object.id])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class SchoolYearDetailView(LoginRequiredMixin, DetailView):
    def get_queryset(self):
        user = self.request.user
        return SchoolYear.objects.filter(school__admin=user).prefetch_related(
            "breaks", "grade_levels"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_link"] = "school_year"

        today = self.request.user.get_local_today()
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


class SchoolYearEditView(LoginRequiredMixin, UpdateView):
    form_class = SchoolYearForm
    template_name = "schools/schoolyear_form.html"

    def get_queryset(self):
        user = self.request.user
        return SchoolYear.objects.filter(school=user.school)

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


class SchoolYearForecastView(LoginRequiredMixin, TemplateView):
    template_name = "schools/schoolyear_forecast.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        school_year = get_object_or_404(
            SchoolYear.objects.filter(school__admin=user), pk=self.kwargs["pk"]
        )
        context["schoolyear"] = school_year

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

        context["students"] = students
        return context


class SchoolYearListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        user = self.request.user
        return SchoolYear.objects.filter(school__admin=user).order_by("-start_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_link"] = "school_year"
        return context


class GradeLevelCreateView(LoginRequiredMixin, CreateView):
    form_class = GradeLevelForm
    template_name = "schools/gradelevel_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        user = self.request.user
        context["school_year"] = get_object_or_404(
            SchoolYear.objects.filter(school__admin=user), pk=self.kwargs["pk"]
        )
        return context

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.kwargs["pk"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class GradeLevelDetailView(LoginRequiredMixin, DetailView):
    def get_queryset(self):
        user = self.request.user
        return GradeLevel.objects.filter(
            school_year__school__admin=user
        ).select_related("school_year")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_year = self.object.school_year
        context["school_year"] = school_year
        context["enrollments"] = self.object.enrollments.select_related("student").all()
        context["show_enroll_cta"] = Enrollment.has_unenrolled_students(school_year)
        return context


class GradeLevelUpdateView(LoginRequiredMixin, UpdateView):
    form_class = GradeLevelForm
    template_name = "schools/gradelevel_form.html"

    def get_queryset(self):
        user = self.request.user
        return GradeLevel.objects.filter(
            school_year__school=user.school
        ).select_related("school_year")

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
    grade_level = get_object_or_404(
        GradeLevel, pk=grade_level_id, school_year__school__admin=user
    )
    course = grade_level.courses.get(id=course_id)
    getattr(grade_level, direction)(course)

    if next_url is None:
        next_url = reverse("schools:grade_level_edit", args=[grade_level_id])
    return HttpResponseRedirect(next_url)


@login_required
@require_POST
def move_course_down(request, pk, course_id):
    """Move a course down in the ordering."""
    return move_course(
        request.user, pk, course_id, "move_course_down", request.GET.get("next")
    )


@login_required
@require_POST
def move_course_up(request, pk, course_id):
    """Move a course up in the ordering."""
    return move_course(
        request.user, pk, course_id, "move_course_up", request.GET.get("next")
    )


class SchoolBreakCreateView(LoginRequiredMixin, CreateView):
    form_class = SchoolBreakForm
    template_name = "schools/schoolbreak_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        user = self.request.user
        school_year = get_object_or_404(
            SchoolYear.objects.filter(school__admin=user), pk=self.kwargs["pk"]
        )
        context["school_year"] = school_year
        context["students"] = Enrollment.get_students_for_school_year(school_year)
        return context

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.kwargs["pk"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class SchoolBreakUpdateView(LoginRequiredMixin, UpdateView):
    form_class = SchoolBreakForm
    template_name = "schools/schoolbreak_form.html"

    def get_queryset(self):
        user = self.request.user
        return SchoolBreak.objects.filter(
            school_year__school=user.school
        ).select_related("school_year")

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


class SchoolBreakDeleteView(LoginRequiredMixin, DeleteView):
    def get_queryset(self):
        user = self.request.user
        return SchoolBreak.objects.filter(
            school_year__school=user.school
        ).select_related("school_year")

    def get_success_url(self):
        return reverse("schools:school_year_detail", args=[self.object.school_year.id])
