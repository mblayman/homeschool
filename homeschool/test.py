from typing import Generic, TypeVar

import factory
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


T = TypeVar("T")


class Factory(Generic[T], factory.django.DjangoModelFactory):
    """A type-aware factory

    https://github.com/FactoryBoy/factory_boy/issues/468#issuecomment-759452373
    """

    @classmethod
    def create(cls, **kwargs) -> T:
        return super().create(**kwargs)

    @classmethod
    def build(cls, **kwargs) -> T:
        return super().build(**kwargs)
