from dataclasses import asdict
from io import BytesIO

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from weasyprint import CSS, HTML

from .contexts import ProgressReportContext, ResourceReportContext


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
    """Make a resource report for the given student.

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
