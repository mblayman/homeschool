import factory


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Account"

    user = factory.SubFactory("homeschool.users.tests.factories.UserFactory")
