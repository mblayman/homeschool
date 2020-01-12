import factory


class SchoolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "schools.School"

    admin = factory.SubFactory("homeschool.users.tests.factories.UserFactory")
