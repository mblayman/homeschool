from homeschool.schools.tests.factories import GradeLevelFactory
from homeschool.students.forms import EnrollmentForm
from homeschool.students.tests.factories import EnrollmentFactory
from homeschool.test import TestCase


class TestEnrollmentForm(TestCase):
    def test_students_only_enroll_in_one_grade_level_per_year(self):
        """A student can only be enrolled in a single grade level in a school year."""
        user = self.make_user()
        enrollment = EnrollmentFactory(
            student__school=user.school, grade_level__school_year__school=user.school
        )
        another_grade_level = GradeLevelFactory(
            school_year=enrollment.grade_level.school_year
        )
        data = {
            "student": str(enrollment.student.id),
            "grade_level": str(another_grade_level.id),
        }
        form = EnrollmentForm(user=user, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert (
            "A student may not be enrolled in multiple grade levels in a school year. "
            f"{enrollment.student} is enrolled in {enrollment.grade_level}."
            in form.non_field_errors()
        )
