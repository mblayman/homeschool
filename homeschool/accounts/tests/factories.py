import factory
from djstripe.models import Event, Price, Product


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Account"

    user = factory.SubFactory("homeschool.users.tests.factories.UserFactory")


# djstripe factories


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    id = factory.Sequence(lambda n: f"evt_{n}")
    data = factory.LazyFunction(lambda: {})


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    id = factory.Sequence(lambda n: f"product_{n}")


class PriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Price

    id = factory.Sequence(lambda n: f"price_{n}")
    active = True
    livemode = False
    product = factory.SubFactory(ProductFactory)
