import factory
from django.utils import timezone

from ..models import Enrollment, Student


class StudentFactory(factory.django.DjangoModelFactory[Student]):
    class Meta:
        model = Student

    school = factory.SubFactory("homeschool.schools.tests.factories.SchoolFactory")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class EnrollmentFactory(factory.django.DjangoModelFactory[Enrollment]):
    class Meta:
        model = "students.Enrollment"

    student = factory.SubFactory(StudentFactory)
    grade_level = factory.SubFactory(
        "homeschool.schools.tests.factories.GradeLevelFactory"
    )


class CourseworkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "students.Coursework"

    student = factory.SubFactory(StudentFactory)
    course_task = factory.SubFactory(
        "homeschool.courses.tests.factories.CourseTaskFactory"
    )
    completed_date = factory.LazyFunction(lambda: timezone.now().date())


class GradeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "students.Grade"

    student = factory.SubFactory(StudentFactory)
    graded_work = factory.SubFactory(
        "homeschool.courses.tests.factories.GradedWorkFactory"
    )
