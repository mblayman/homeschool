from django_extensions.management.jobs import HourlyJob

from homeschool.reports import pdfs
from homeschool.reports.models import Bundle


class Job(HourlyJob):
    """Build any pending PDF bundles."""

    help = __doc__

    def execute(self):
        processed = 0

        for bundle in Bundle.objects.pending().select_related("school_year"):
            report_data = pdfs.make_bundle(bundle.school_year)
            bundle.store(report_data)
            processed += 1

        return processed
