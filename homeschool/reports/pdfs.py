from dataclasses import asdict
from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.template.loader import render_to_string
from django.templatetags.static import static
from weasyprint import CSS, HTML

from .contexts import ResourceReportContext


def make_resource_report(context: ResourceReportContext) -> bytes:
    """Make a resource report for the given student.

    Return raw PDF data.
    """
    # TODO: Needs tests.
    site_css = static("site.css")
    site_css_path = settings.STATIC_ROOT / site_css.replace(settings.STATIC_URL, "")
    site_css_path = staticfiles_storage.path("site.css")
    rendered = render_to_string("reports/resource_report_pdf.html", asdict(context))
    html = HTML(string=rendered)
    io = BytesIO()
    html.write_pdf(io, stylesheets=[CSS(site_css_path)])
    return io.getvalue()
