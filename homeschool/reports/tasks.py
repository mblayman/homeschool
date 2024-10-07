from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from homeschool.reports import pdfs
from homeschool.reports.models import Bundle


@db_periodic_task(crontab(minute="0"))
def build_bundle():
    """Build any pending PDF bundles."""
    for bundle in Bundle.objects.pending().select_related("school_year"):
        print(f"Processing {bundle.school_year.id}...")
        report_data = pdfs.make_bundle(bundle.school_year)
        bundle.store(report_data)
