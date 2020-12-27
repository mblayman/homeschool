from homeschool.notifications.models import Notification
from homeschool.notifications.tests.factories import NotificationFactory
from homeschool.test import TestCase


class TestSendToWhatsNew(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("notifications:whats_new")

    def test_get(self):
        user = self.make_user()
        notification = NotificationFactory(user=user)

        with self.login(user):
            response = self.get("notifications:whats_new")

        assert response.status_code == 302
        assert response["Location"] == notification.announcement.url

    def test_latest_notification(self):
        """The redirect goes to the latest notification announcement URL."""
        user = self.make_user()
        NotificationFactory(user=user)
        notification = NotificationFactory(user=user)

        with self.login(user):
            response = self.get("notifications:whats_new")

        assert response["Location"] == notification.announcement.url

    def test_no_notifications(self):
        """When there are no notifications, send to the app view."""
        user = self.make_user()

        with self.login(user):
            response = self.get("notifications:whats_new")

        assert response.status_code == 302
        assert response["Location"] == self.reverse("core:dashboard")

    def test_marks_all_notifications_viewed(self):
        """Any unread notifications from the user are marked as viewed."""
        user = self.make_user()
        NotificationFactory()  # Ensure a different user isn't affected.
        NotificationFactory(user=user)
        unread = Notification.NotificationStatus.UNREAD

        with self.login(user):
            self.get("notifications:whats_new")

        assert Notification.objects.filter(user=user, status=unread).count() == 0
        assert Notification.objects.filter(status=unread).count() == 1
