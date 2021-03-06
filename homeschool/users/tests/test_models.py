from django.conf import settings
from django.core import mail

from homeschool.accounts.models import Account
from homeschool.schools.models import School
from homeschool.schools.tests.factories import SchoolFactory
from homeschool.test import TestCase
from homeschool.users.models import notify_signup


class TestUser(TestCase):
    def test_school(self):
        user = self.make_user()
        SchoolFactory(admin=user)
        school = SchoolFactory(admin=user)

        assert user.school == school

    def test_create_school(self):
        """A new user automatically has a school created."""
        user = self.make_user()

        assert user.school == School.objects.get(admin=user)

    def test_create_account(self):
        """A new user automatically has an account created."""
        user = self.make_user()

        assert Account.objects.filter(user=user).exists()


class TestProfile(TestCase):
    def test_user_has_profile(self):
        """Every user has a profile record."""
        user = self.make_user()

        assert user.profile is not None

    def test_wants_announcements(self):
        """By default, users receive announcement notifications."""
        user = self.make_user()

        assert user.profile.wants_announcements

    def test_str(self):
        user = self.make_user()

        assert str(user.profile) == f"Profile for {user.username}"


class TestNotifySignup(TestCase):
    def test_signup_sends_email(self):
        """A signup sends an email to the support address."""
        user = self.make_user()

        notify_signup(user, request=None, user=user)

        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert user.username in message.subject
        assert message.to == [settings.SUPPORT_EMAIL]
