from homeschool.notifications.models import Announcement, Notification
from homeschool.notifications.tests.factories import (
    AnnouncementFactory,
    NotificationFactory,
)
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


class TestNotification(TestCase):
    def test_factory(self):
        notification = NotificationFactory()

        assert notification.status == Notification.NotificationStatus.UNREAD
        assert notification.created_at is not None
        assert notification.user is not None
        assert notification.announcement is not None

    def test_str(self):
        notification = NotificationFactory()

        assert (
            str(notification)
            == f"Notification for {notification.user} for {notification.announcement}"
        )
