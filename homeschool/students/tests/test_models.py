from homeschool.schools.tests.factories import GradeLevelFactory, SchoolFactory
from homeschool.students.tests.factories import EnrollmentFactory, StudentFactory
from homeschool.test import TestCase


class TestStudent(TestCase):
    def test_factory(self):
        student = StudentFactory()

        self.assertIsNotNone(student)
        self.assertNotEqual(student.first_name, "")
        self.assertNotEqual(student.last_name, "")

    def test_has_school(self):
        school = SchoolFactory()
        student = StudentFactory(school=school)

        self.assertEqual(student.school, school)

    def test_has_first_name(self):
        first_name = "James"
        student = StudentFactory(first_name=first_name)

        self.assertEqual(student.first_name, first_name)

    def test_has_last_name(self):
        last_name = "Bond"
        student = StudentFactory(last_name=last_name)

        self.assertEqual(student.last_name, last_name)

    def test_full_name(self):
        student = StudentFactory()

        self.assertEqual(student.full_name, f"{student.first_name} {student.last_name}")

    def test_str(self):
        student = StudentFactory()

        self.assertEqual(str(student), student.full_name)


class TestEnrollment(TestCase):
    def test_factory(self):
        enrollment = EnrollmentFactory()

        self.assertIsNotNone(enrollment)

    def test_has_student(self):
        student = StudentFactory()
        enrollment = EnrollmentFactory(student=student)

        self.assertEqual(enrollment.student, student)

    def test_has_grade_level(self):
        grade_level = GradeLevelFactory()
        enrollment = EnrollmentFactory(grade_level=grade_level)

        self.assertEqual(enrollment.grade_level, grade_level)
