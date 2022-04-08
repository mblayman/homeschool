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
