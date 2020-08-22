import factory
from django.conf import settings


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL

    username = factory.Sequence(lambda n: f"user_{n}")
    # Test plus uses "password" to permit login.
    # By setting this here, UserFactory can be used to create staff and superusers
    # that can still log in.
    password = factory.PostGenerationMethodCall("set_password", "password")
