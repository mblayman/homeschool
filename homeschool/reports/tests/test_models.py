from homeschool.reports.models import Bundle
from homeschool.reports.tests.factories import BundleFactory
from homeschool.test import TestCase


class TestBundle(TestCase):
    def test_instance(self):
        bundle = BundleFactory()

        assert bundle.created_at is not None
        assert bundle.updated_at is not None
        assert bundle.report is not None
        assert bundle.status == Bundle.Status.PENDING

    def test_stores_report_data(self):
        """The bundle stores the report data."""
        bundle = BundleFactory(status=Bundle.Status.PENDING)
        report_data = b"report"

        bundle.store(report_data)

        bundle.refresh_from_db()
        assert bundle.status == Bundle.Status.COMPLETE
        assert bundle.report.read() == report_data
