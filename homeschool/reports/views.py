import datetime
import io
import zipfile
from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from homeschool.courses.models import CourseResource
from homeschool.schools.models import SchoolYear
from homeschool.students.models import Coursework, Enrollment, Grade


class ReportsIndexView(LoginRequiredMixin, TemplateView):
    template_name = "reports/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_link"] = "reports"

        user = self.request.user
        context["enrollments"] = (
            Enrollment.objects.filter(grade_level__school_year__school__admin=user)
            .select_related("student", "grade_level", "grade_level__school_year")
            .order_by("-grade_level__school_year__start_date", "student")
        )
        context["school_years"] = SchoolYear.objects.filter(
            school__admin=user
        ).order_by("-start_date")
        return context


class BundleView(LoginRequiredMixin, TemplateView):
    template_name = "reports/bundle.html"

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context["school_year"] = get_object_or_404(
            SchoolYear, pk=self.kwargs["pk"], school__admin=user
        )
        return context


@login_required
def create_bundle(request, pk):
    user = request.user
    get_object_or_404(SchoolYear, pk=pk, school__admin=user)

    zip_file_data = io.BytesIO()
    with zipfile.ZipFile(zip_file_data, "w") as zip_file:
        zip_file.writestr("file1.txt", b"hello world")
        zip_file.writestr("file2.txt", b"hello world")

    filename = "bundle.zip"
    return HttpResponse(
        zip_file_data.getbuffer(),
        headers={
            "Content-Type": "application/zip",
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


class AttendanceReportView(LoginRequiredMixin, TemplateView):
    template_name = "reports/attendance_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "student", "grade_level", "grade_level__school_year"
            ),
            pk=self.kwargs["pk"],
            grade_level__school_year__school=user.school,
        )
        context["grade_level"] = enrollment.grade_level
        context["school_year"] = enrollment.grade_level.school_year
        context["student"] = enrollment.student
        context["school_dates"] = self._build_school_dates(enrollment)
        context["total_days_attended"] = sum(
            1 for school_date in context["school_dates"] if school_date["attended"]
        )
        return context

    def _build_school_dates(self, enrollment):
        """Collect all the school dates in the year to the end or today."""
        dates_with_work = set(
            Coursework.objects.filter(
                student=enrollment.student,
                course_task__course__grade_levels__in=[enrollment.grade_level],
            ).values_list("completed_date", flat=True)
        )
        school_dates = []
        school_year = enrollment.grade_level.school_year
        school_date = school_year.start_date
        end_date = min(school_year.end_date, self.request.user.get_local_today())
        while school_date <= end_date:
            school_dates.append(
                {
                    "date": school_date,
                    "is_school_day": school_year.runs_on(school_date),
                    "is_break": school_year.is_break(
                        school_date, student=enrollment.student
                    ),
                    "attended": school_date in dates_with_work,
                }
            )
            school_date += datetime.timedelta(days=1)
        return school_dates


class ProgressReportView(LoginRequiredMixin, TemplateView):
    template_name = "reports/progress_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "student", "grade_level", "grade_level__school_year"
            ),
            pk=self.kwargs["pk"],
            grade_level__school_year__school=user.school,
        )
        context["grade_level"] = enrollment.grade_level
        context["school_year"] = enrollment.grade_level.school_year
        context["student"] = enrollment.student

        course_id = self.request.GET.get("course")
        if course_id:
            qs_filter = Q(graded_work__course_task__course__id=course_id)
        else:
            qs_filter = Q(
                graded_work__course_task__course__grade_levels__in=[
                    enrollment.grade_level
                ]
            )

        grades = (
            Grade.objects.filter(qs_filter, student=enrollment.student)
            # Include secondary ordering so tasks are ordered in the course.
            .order_by(
                "graded_work__course_task__course", "graded_work__course_task"
            ).select_related(
                "graded_work__course_task", "graded_work__course_task__course"
            )
        )

        self._mixin_coursework(grades, enrollment.student)
        context["courses"] = self._build_courses_info(grades)
        return context

    def _mixin_coursework(self, grades, student):
        """Mix in the coursework for the grades.

        Coursework is added to the grades to display the completed dates.
        It is possible for a user to add a grade without the student finishing the task
        so the coursework can be None.
        """
        tasks = [grade.graded_work.course_task for grade in grades]
        coursework_by_task_id = {
            coursework.course_task_id: coursework
            for coursework in Coursework.objects.filter(
                student=student, course_task__in=tasks
            )
        }
        for grade in grades:
            grade.coursework = coursework_by_task_id.get(
                grade.graded_work.course_task_id
            )

    def _build_courses_info(self, grades):
        """Regroup the grades into an appropriate display structure for the template.

        Grades must be sorted by course.
        """
        if not grades:
            return []

        courses = []
        course = None
        course_info = {}
        for grade in grades:
            next_course = grade.graded_work.course_task.course
            if course != next_course:
                # Don't compute average until a course is collected.
                # On the first iteration when course is None, nothing is collected yet.
                if course is not None:
                    self._compute_course_average(course_info)
                course = next_course
                course_info = {"course": course, "grades": [grade]}
                courses.append(course_info)
            else:
                course_info["grades"].append(grade)

        # Compute average of last course to catch the edge case.
        self._compute_course_average(course_info)
        return courses

    def _compute_course_average(self, course_info):
        """Compute the average for the course based on collected grades."""
        grades = course_info["grades"]
        average = sum(grade.score for grade in grades) / len(grades)
        # Sane rounding.
        course_info["course_average"] = int(Decimal(average).quantize(0, ROUND_HALF_UP))


class ResourceReportView(LoginRequiredMixin, TemplateView):
    template_name = "reports/resource_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "student", "grade_level", "grade_level__school_year"
            ),
            pk=self.kwargs["pk"],
            grade_level__school_year__school=user.school,
        )
        context["grade_level"] = enrollment.grade_level
        context["school_year"] = enrollment.grade_level.school_year
        context["student"] = enrollment.student
        context["resources"] = (
            CourseResource.objects.filter(
                course__grade_levels__in=[enrollment.grade_level]
            )
            .select_related("course")
            .order_by("course")
        )
        return context
