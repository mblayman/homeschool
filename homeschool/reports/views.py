from dataclasses import asdict

from denied.authorizers import any_authorized, staff_authorized
from denied.decorators import authorize
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from homeschool.schools.authorizers import school_year_authorized
from homeschool.schools.models import SchoolYear
from homeschool.students.authorizers import enrollment_authorized
from homeschool.students.models import Enrollment

from . import pdfs
from .contexts import (
    AttendanceReportContext,
    CourseworkReportContext,
    ProgressReportContext,
    ResourceReportContext,
)
from .models import Bundle


@authorize(staff_authorized)
def office_pdfs_dashboard(request):
    context: dict = {}
    return render(request, "reports/pdfs_dashboard.html", context)


@authorize(any_authorized)
def reports_index(request):
    enrollments = (
        Enrollment.objects.filter(grade_level__school_year__school__admin=request.user)
        .select_related("student", "grade_level", "grade_level__school_year")
        .order_by("-grade_level__school_year__start_date", "student")
    )
    context = {
        "nav_link": "reports",
        "enrollments": enrollments,
        "school_years": SchoolYear.objects.filter(school__admin=request.user).order_by(
            "-start_date"
        ),
    }
    return render(request, "reports/index.html", context)


@authorize(school_year_authorized)
def get_bundle(request, pk):
    """Let a user get the bundle or request the creation of a bundle."""
    school_year = SchoolYear.objects.get(pk=pk)

    if request.method == "POST":
        bundle, _ = Bundle.objects.get_or_create(school_year=school_year)

        if bundle and request.POST.get("recreate"):
            bundle.recreate()

        return HttpResponseRedirect(reverse("reports:bundle", args=[school_year.id]))

    bundle = Bundle.objects.by_school_year(school_year)  # type: ignore  # Issue 762
    context = {"bundle": bundle, "school_year": school_year}
    return render(request, "reports/bundle.html", context)


@require_POST
@authorize(staff_authorized)
def office_attendance_report(request):
    enrollment_id = request.POST["enrollment_id"]
    enrollment = get_object_or_404(
        Enrollment.objects.select_related(
            "student", "grade_level", "grade_level__school_year"
        ),
        pk=enrollment_id,
    )
    context = AttendanceReportContext.from_enrollment(
        enrollment, request.user.get_local_today()
    )
    pdf_data = pdfs.make_attendance_report(context)
    return HttpResponse(
        pdf_data,
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="attendance-report.pdf"',
        },
    )


@authorize(enrollment_authorized)
def attendance_report(request, pk):
    enrollment = Enrollment.objects.select_related(
        "student", "grade_level", "grade_level__school_year"
    ).get(pk=pk)
    today = request.user.get_local_today()
    context = asdict(AttendanceReportContext.from_enrollment(enrollment, today))
    return render(request, "reports/attendance_report.html", context)


@require_POST
@authorize(staff_authorized)
def office_coursework_report(request):
    enrollment_id = request.POST["enrollment_id"]
    enrollment = get_object_or_404(
        Enrollment.objects.select_related(
            "student", "grade_level", "grade_level__school_year"
        ),
        pk=enrollment_id,
    )
    context = CourseworkReportContext.from_enrollment(enrollment)
    pdf_data = pdfs.make_coursework_report(context)
    return HttpResponse(
        pdf_data,
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="coursework-report.pdf"',
        },
    )


@require_POST
@authorize(staff_authorized)
def office_progress_report(request):
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


@authorize(enrollment_authorized)
def progress_report(request, pk):
    enrollment = Enrollment.objects.select_related(
        "student", "grade_level", "grade_level__school_year"
    ).get(pk=pk)
    context = asdict(
        ProgressReportContext.from_enrollment(enrollment, request.GET.get("course"))
    )
    return render(request, "reports/progress_report.html", context)


@require_POST
@authorize(staff_authorized)
def office_resource_report(request):
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


@authorize(enrollment_authorized)
def resource_report(request, pk):
    enrollment = Enrollment.objects.select_related(
        "student", "grade_level", "grade_level__school_year"
    ).get(pk=pk)
    context = asdict(ResourceReportContext.from_enrollment(enrollment))
    return render(request, "reports/resource_report.html", context)
