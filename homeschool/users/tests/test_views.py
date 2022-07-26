from homeschool.test import TestCase


class TestSettingsDashboard(TestCase):
    def test_ok(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("settings:dashboard")

        assert self.get_context("nav_link") == "settings"
        assert self.get_context("referral_form") is not None

    def test_wants_announcements_change(self):
        """The wants announcement profile setting can change."""
        user = self.make_user()
        data: dict = {}

        with self.login(user):
            response = self.post("settings:dashboard", data=data)

        assert response.status_code == 302
        assert response["Location"] == self.reverse("settings:dashboard")
        user.profile.refresh_from_db()
        assert not user.profile.wants_announcements
