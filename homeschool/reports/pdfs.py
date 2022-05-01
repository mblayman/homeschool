import zipfile
from dataclasses import asdict
from io import BytesIO

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import CSS, HTML

from homeschool.schools.models import SchoolYear
from homeschool.students.models import Enrollment

from .contexts import (
    AttendanceReportContext,
    CourseworkReportContext,
    ProgressReportContext,
    ResourceReportContext,
)


def make_bundle(school_year: SchoolYear) -> bytes:
    """Make the zip file bundle."""
    enrollments = Enrollment.objects.filter(
        grade_level__school_year=school_year
    ).select_related("student", "grade_level", "grade_level__school_year")

    zip_file_data = BytesIO()
    with zipfile.ZipFile(zip_file_data, "w") as zip_file:
        for enrollment in enrollments:
            attendance_context = AttendanceReportContext.from_enrollment(
                enrollment, timezone.localdate()
            )
            name = f"{school_year} - {enrollment.student} Attendance Report.pdf"
            zip_file.writestr(name, make_attendance_report(attendance_context))

            coursework_context = CourseworkReportContext.from_enrollment(enrollment)
            name = f"{school_year} - {enrollment.student} Courses Report.pdf"
            zip_file.writestr(name, make_coursework_report(coursework_context))

            progress_context = ProgressReportContext.from_enrollment(enrollment)
            name = f"{school_year} - {enrollment.student} Progress Report.pdf"
            zip_file.writestr(name, make_progress_report(progress_context))

            resource_context = ResourceReportContext.from_enrollment(enrollment)
            name = f"{school_year} - {enrollment.student} Resource Report.pdf"
            zip_file.writestr(name, make_resource_report(resource_context))

    return zip_file_data.getbuffer()


def make_attendance_report(context: AttendanceReportContext) -> bytes:
    """Make an attendance report for the given student.

    Return raw PDF data.
    """
    return _make_report("reports/attendance_report_pdf.html", asdict(context))


def make_coursework_report(context: CourseworkReportContext) -> bytes:
    """Make a coursework report for the given student.

    Return raw PDF data.
    """
    return _make_report("reports/coursework_report_pdf.html", asdict(context))


def make_progress_report(context: ProgressReportContext) -> bytes:
    """Make a progress report for the given student.

    Return raw PDF data.
    """
    return _make_report("reports/progress_report_pdf.html", asdict(context))


def make_resource_report(context: ResourceReportContext) -> bytes:
    """Make a resource report for the given student.

    Return raw PDF data.
    """
    return _make_report("reports/resource_report_pdf.html", asdict(context))


def _make_report(template_name: str, context: dict) -> bytes:
    """Make a report.

    Return raw PDF data.
    """
    site_css_path = finders.find("site.css")
    with open(site_css_path) as f:
        css_content = f.read()
    # Weasyprint doesn't render the Tailwind font properly.
    # The default font failed to render numbers.
    # Use a safe, albeit boring, font of Arial.
    css_content += "\nhtml { font-family: Arial; }"

    rendered = render_to_string(template_name, context)
    html = HTML(string=rendered)
    io = BytesIO()
    html.write_pdf(io, stylesheets=[CSS(string=css_content)])
    return io.getvalue()
