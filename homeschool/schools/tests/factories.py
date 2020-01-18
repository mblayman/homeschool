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
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(
        lambda: timezone.now().date() + datetime.timedelta(days=365)
    )


class GradeLevelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "schools.GradeLevel"

    school_year = factory.SubFactory(SchoolYearFactory)
