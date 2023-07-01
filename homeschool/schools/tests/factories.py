import datetime

import factory
from django.utils import timezone


class SchoolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "schools.School"

    admin = factory.SubFactory("homeschool.users.tests.factories.UserFactory")


class SchoolYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "schools.SchoolYear"

    school = factory.SubFactory(SchoolFactory)
    start_date = factory.LazyFunction(
        lambda: timezone.localdate() - datetime.timedelta(days=30)
    )
    end_date = factory.LazyFunction(
        lambda: timezone.localdate() + datetime.timedelta(days=340)
    )


class GradeLevelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "schools.GradeLevel"

    name = factory.Sequence(lambda n: f"{n} Grade")
    school_year = factory.SubFactory(SchoolYearFactory)


class SchoolBreakFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "schools.SchoolBreak"

    start_date = factory.LazyFunction(lambda: timezone.localdate())
    end_date = factory.LazyFunction(
        lambda: timezone.localdate() + datetime.timedelta(days=5)
    )
    description = factory.Faker("sentence")
    school_year = factory.SubFactory(SchoolYearFactory)
