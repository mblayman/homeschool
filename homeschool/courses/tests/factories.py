import factory


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.Course"

    name = factory.Sequence(lambda n: f"Course {n}")
    grade_level = factory.SubFactory(
        "homeschool.schools.tests.factories.GradeLevelFactory"
    )


class CourseTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.CourseTask"

    course = factory.SubFactory(CourseFactory)
    description = factory.Faker("sentence")
    duration = factory.Faker("pyint", min_value=0, max_value=60)


class GradedWorkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.GradedWork"

    course_task = factory.SubFactory(CourseTaskFactory)
