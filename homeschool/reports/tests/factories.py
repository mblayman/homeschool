import factory


class BundleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "reports.Bundle"

    school_year = factory.SubFactory(
        "homeschool.schools.tests.factories.SchoolYearFactory"
    )
    report = factory.django.FileField()
