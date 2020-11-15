from homeschool.notifications.models import Announcement
from homeschool.notifications.tests.factories import AnnouncementFactory
from homeschool.test import TestCase


class TestAnnouncement(TestCase):
    def test_factory(self):
        announcement = AnnouncementFactory()

        assert announcement.status == Announcement.AnnouncementStatus.PENDING
        assert announcement.created_at is not None
        assert announcement.url is not None

    def test_str(self):
        announcement = AnnouncementFactory()

        assert str(announcement) == announcement.url
