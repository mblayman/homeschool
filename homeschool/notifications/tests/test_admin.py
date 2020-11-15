import responses
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.messages import get_messages
from django.contrib.sites.models import Site

from homeschool.accounts.models import Account
from homeschool.notifications.models import Announcement, Notification
from homeschool.notifications.tests.factories import AnnouncementFactory
from homeschool.test import TestCase
from homeschool.users.tests.factories import UserFactory


class TestAnnouncementAdmin(TestCase):
    list_url = "admin:notifications_announcement_changelist"

    def test_single_announcement(self):
        """Only one announcement can be announced."""
        pending = Announcement.AnnouncementStatus.PENDING
        announcement = AnnouncementFactory(status=pending)
        other_announcement = AnnouncementFactory(status=pending)
        user = UserFactory(is_staff=True, is_superuser=True)
        data = {
            "action": "announce",
            ACTION_CHECKBOX_NAME: [str(announcement.id), str(other_announcement.id)],
        }

        with self.login(user):
            response = self.post(self.list_url, data=data)

        message = list(get_messages(response.wsgi_request))[0]
        assert str(message) == "Select one."
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "admin:notifications_announcement_changelist"
        )

    def test_announce_only_pending(self):
        """Only pending announcements can be announced."""
        announced = Announcement.AnnouncementStatus.ANNOUNCED
        announcement = AnnouncementFactory(status=announced)
        user = UserFactory(is_staff=True, is_superuser=True)
        data = {"action": "announce", ACTION_CHECKBOX_NAME: str(announcement.id)}

        with self.login(user):
            response = self.post(self.list_url, data=data)

        message = list(get_messages(response.wsgi_request))[0]
        assert str(message) == "That announcement is already announced."

    @responses.activate
    def test_check_for_invalid_url(self):
        """The URL is checked to be valid and rejected when bad."""
        pending = Announcement.AnnouncementStatus.PENDING
        announcement = AnnouncementFactory(status=pending)
        site = Site.objects.get_current()
        url = f"http://{site}{announcement.url}"
        responses.add(responses.GET, url, status=404)
        user = UserFactory(is_staff=True, is_superuser=True)
        data = {"action": "announce", ACTION_CHECKBOX_NAME: str(announcement.id)}

        with self.login(user):
            response = self.post(self.list_url, data=data)

        message = list(get_messages(response.wsgi_request))[0]
        assert str(message) == "The announcement URL was a non-200 response."
        self.response_302(response)
        assert response.get("Location") == self.reverse(
            "admin:notifications_announcement_changelist"
        )

    @responses.activate
    def test_notifications_created(self):
        """Notifications are created for those that want them."""
        pending = Announcement.AnnouncementStatus.PENDING
        announcement = AnnouncementFactory(status=pending)
        site = Site.objects.get_current()
        url = f"http://{site}{announcement.url}"
        responses.add(responses.GET, url, status=200)
        user = UserFactory(is_staff=True, is_superuser=True)
        # Skip users that don't want it.
        non_announced_user = UserFactory()
        non_announced_user.profile.wants_announcements = False
        non_announced_user.profile.save()
        # Skip canceled users.
        canceled_user = UserFactory()
        canceled = Account.AccountStatus.CANCELED
        Account.objects.filter(user=canceled_user).update(status=canceled)
        data = {"action": "announce", ACTION_CHECKBOX_NAME: str(announcement.id)}

        with self.login(user):
            self.post(self.list_url, data=data)

        assert Notification.objects.filter(announcement=announcement).count() == 1
        notification = Notification.objects.filter(announcement=announcement).first()
        assert notification.user == user

    @responses.activate
    def test_announcement_announced(self):
        """An announcement is marked as announced."""
        pending = Announcement.AnnouncementStatus.PENDING
        announcement = AnnouncementFactory(status=pending)
        site = Site.objects.get_current()
        url = f"http://{site}{announcement.url}"
        responses.add(responses.GET, url, status=200)
        user = UserFactory(is_staff=True, is_superuser=True)
        data = {"action": "announce", ACTION_CHECKBOX_NAME: str(announcement.id)}

        with self.login(user):
            self.post(self.list_url, data=data)

        announcement.refresh_from_db()
        assert announcement.status == Announcement.AnnouncementStatus.ANNOUNCED
