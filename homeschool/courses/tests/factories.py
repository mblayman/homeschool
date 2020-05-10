import factory


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.Course"

    name = factory.Sequence(lambda n: f"Course {n}")

    @factory.post_generation
    def grade_levels(course, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            course.grade_levels.set(extracted)


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
