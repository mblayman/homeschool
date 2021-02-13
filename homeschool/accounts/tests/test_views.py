from homeschool.test import TestCase


class TestSubscriptionsView(TestCase):
    def test_unauthenticated_access(self):
        self.assertLoginRequired("subscriptions:index")

    def test_get(self):
        user = self.make_user()

        with self.login(user):
            self.get_check_200("subscriptions:index")
