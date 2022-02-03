from dataclasses import asdict
from io import BytesIO

from django.template.loader import render_to_string
from weasyprint import HTML

from .contexts import ResourceReportContext


def make_resource_report(context: ResourceReportContext) -> bytes:
    """Make a resource report for the given student.

    Return raw PDF data.
    """
    # TODO: Needs tests.
    rendered = render_to_string("reports/resource_report_pdf.html", asdict(context))
    html = HTML(string=rendered)
    io = BytesIO()
    html.write_pdf(io)
    return io.getvalue()
