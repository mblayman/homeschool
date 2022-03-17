import datetime
import io
import zipfile
from dataclasses import asdict

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from homeschool.schools.models import SchoolYear
from homeschool.students.models import Coursework, Enrollment

from . import pdfs
from .contexts import ProgressReportContext, ResourceReportContext


@staff_member_required
def pdfs_dashboard(request):
    context: dict = {}
    return render(request, "reports/pdfs_dashboard.html", context)


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
    """Create a bundle of year end PDF reports."""
    user = request.user
    school_year = get_object_or_404(SchoolYear, pk=pk, school__admin=user)

    enrollments = Enrollment.objects.filter(
        grade_level__school_year=school_year
    ).select_related("student", "grade_level", "grade_level__school_year")

    zip_file_data = io.BytesIO()
    with zipfile.ZipFile(zip_file_data, "w") as zip_file:
        for enrollment in enrollments:
            progress_report_context = ProgressReportContext.from_enrollment(enrollment)
            zip_file.writestr(
                f"{school_year} - {enrollment.student} Progress Report.pdf",
                pdfs.make_progress_report(progress_report_context),
            )

            resource_report_context = ResourceReportContext.from_enrollment(enrollment)
            zip_file.writestr(
                f"{school_year} - {enrollment.student} Resource Report.pdf",
                pdfs.make_resource_report(resource_report_context),
            )

    filename = f"School Desk bundle {school_year}.zip"
    # The "dash" character is an emdash from the SchoolYear.__str__ method.
    # Replace with a regular dash to avoid header character encoding weirdness.
    filename = filename.replace("–", "-")
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


@staff_member_required
@require_POST
def progress_report(request):
    enrollment_id = request.POST["enrollment_id"]
    enrollment = get_object_or_404(
        Enrollment.objects.select_related(
            "student", "grade_level", "grade_level__school_year"
        ),
        pk=enrollment_id,
    )
    context = ProgressReportContext.from_enrollment(enrollment)
    pdf_data = pdfs.make_progress_report(context)
    return HttpResponse(
        pdf_data,
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="progress-report.pdf"',
        },
    )


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
        progress_report_context = ProgressReportContext.from_enrollment(
            enrollment, self.request.GET.get("course")
        )
        context.update(asdict(progress_report_context))
        return context


@staff_member_required
@require_POST
def resource_report(request):
    enrollment_id = request.POST["enrollment_id"]
    enrollment = get_object_or_404(
        Enrollment.objects.select_related(
            "student", "grade_level", "grade_level__school_year"
        ),
        pk=enrollment_id,
    )
    context = ResourceReportContext.from_enrollment(enrollment)
    pdf_data = pdfs.make_resource_report(context)
    return HttpResponse(
        pdf_data,
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="resource-report.pdf"',
        },
    )


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
        resource_report_context = ResourceReportContext.from_enrollment(enrollment)
        context.update(asdict(resource_report_context))
        return context
