from homeschool.test import TestCase


class TestApp(TestCase):
    def test_ok(self):
        user = self.make_user()
        with self.login(user):
            self.get_check_200("app")

    def test_unauthenticated_access(self):
        self.assertLoginRequired("app")
