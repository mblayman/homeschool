from django.http import HttpResponse
from django.test import RequestFactory
from test_plus.test import TestCase as PlusTestCase

from homeschool.users.tests.factories import UserFactory


def get_response(request):
    """A basic callback for the middleware tests to use."""
    return HttpResponse()


class TestCase(PlusTestCase):
    """A base test case class"""

    rf = RequestFactory()
    user_factory = UserFactory
