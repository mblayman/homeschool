import factory


class ChecklistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "teachers.Checklist"

    school_year = factory.SubFactory(
        "homeschool.schools.tests.factories.SchoolYearFactory"
    )
