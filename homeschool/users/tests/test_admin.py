from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME

from homeschool.test import TestCase
from homeschool.users.tests.factories import UserFactory


class TestUserAdmin(TestCase):
    def test_hijack_user(self):
        """A superuser can hijack another user."""
        hijacked = UserFactory()
        user = UserFactory(is_staff=True, is_superuser=True)
        data = {"action": "hijack_user", ACTION_CHECKBOX_NAME: str(hijacked.id)}

        with self.login(user):
            response = self.post("admin:users_user_changelist", data=data)

        self.response_302(response)
        assert response.get("Location") == self.reverse("core:dashboard")

    def test_multiple_user_hijack_attempt(self):
        """A superuser may not hijack multiple users simultaneously."""
        hijacked = UserFactory()
        other = UserFactory()
        user = UserFactory(is_staff=True, is_superuser=True)
        data = {
            "action": "hijack_user",
            ACTION_CHECKBOX_NAME: [str(hijacked.id), str(other.id)],
        }

        with self.login(user):
            response = self.post("admin:users_user_changelist", data=data)

        self.response_302(response)
        assert response.get("Location") == self.reverse("admin:users_user_changelist")
