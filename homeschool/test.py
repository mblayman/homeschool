from test_plus.test import TestCase as PlusTestCase

from homeschool.users.tests.factories import UserFactory


class TestCase(PlusTestCase):
    """A base test case class"""

    user_factory = UserFactory
