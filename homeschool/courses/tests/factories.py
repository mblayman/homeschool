import factory

from homeschool.test import Factory

from ..models import CourseTask


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.Course"

    name = factory.Sequence(lambda n: f"Course {n}")

    @factory.post_generation
    def grade_levels(course, create, extracted, **kwargs):  # noqa: B902
        if not create:
            return

        if extracted:
            course.grade_levels.set(extracted)


class CourseTaskFactory(Factory[CourseTask]):
    class Meta:
        model = CourseTask

    course = factory.SubFactory(CourseFactory)
    description = factory.Faker("sentence")
    duration = factory.Faker("pyint", min_value=0, max_value=60)


class GradedWorkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.GradedWork"

    course_task = factory.SubFactory(CourseTaskFactory)


class CourseResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.CourseResource"

    course = factory.SubFactory(CourseFactory)
    title = factory.Faker("sentence")
    details = factory.Faker("paragraph")
