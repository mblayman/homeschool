from unittest import mock

from homeschool.reports.jobs import build_bundle
from homeschool.reports.models import Bundle
from homeschool.reports.tests.factories import BundleFactory
from homeschool.test import TestCase


class TestBuildBundle(TestCase):
    @mock.patch("homeschool.reports.jobs.build_bundle.pdfs.make_bundle", autospec=True)
    def test_completes_pending_bundle(self, mock_make_bundle):
        """Any pending bundles are processed."""
        bundle = BundleFactory(status=Bundle.Status.PENDING)
        BundleFactory(status=Bundle.Status.COMPLETE)
        job = build_bundle.Job()
        mock_make_bundle.return_value = b"report"

        processed = job.execute()

        assert processed == 1
        mock_make_bundle.assert_called_once_with(bundle.school_year)
        bundle.refresh_from_db()
        assert bundle.status == Bundle.Status.COMPLETE
