import datetime

from homeschool.courses.models import Course
from homeschool.courses.tests.factories import CourseFactory
from homeschool.schools.forms import SchoolBreakForm, SchoolYearForm
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolBreakFactory,
    SchoolFactory,
    SchoolYearFactory,
)
from homeschool.students.tests.factories import EnrollmentFactory
from homeschool.test import TestCase


class TestSchoolYearForm(TestCase):
    def test_invalid_start_date(self):
        """An invalid start date records a form error."""
        school = SchoolFactory()
        data = {
            "school": str(school.id),
            "start_date": "bogus",
            "end_date": "6/1/2021",
            "monday": True,
        }
        form = SchoolYearForm(user=school.admin, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "start_date" in form.errors

    def test_invalid_end_date(self):
        """An invalid end date records a form error."""
        school = SchoolFactory()
        data = {
            "school": str(school.id),
            "start_date": "9/1/2020",
            "end_date": "bogus",
            "monday": True,
        }
        form = SchoolYearForm(user=school.admin, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "end_date" in form.errors

    def test_no_overlapping_school_years(self):
        """A school year's dates may not overlap with another."""
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)
        cases = [
            (
                "surround",
                str(school_year.start_date - datetime.timedelta(days=1)),
                str(school_year.end_date + datetime.timedelta(days=1)),
            ),
            (
                "inside",
                str(school_year.start_date + datetime.timedelta(days=1)),
                str(school_year.end_date - datetime.timedelta(days=1)),
            ),
            (
                "overlap_start",
                str(school_year.start_date - datetime.timedelta(days=1)),
                str(school_year.end_date - datetime.timedelta(days=1)),
            ),
            (
                "overlap_end",
                str(school_year.start_date + datetime.timedelta(days=1)),
                str(school_year.end_date + datetime.timedelta(days=1)),
            ),
        ]

        for case in cases:
            with self.subTest(case[0]):
                data = {
                    "school": str(school.id),
                    "start_date": case[1],
                    "end_date": case[2],
                    "monday": True,
                }
                form = SchoolYearForm(user=school.admin, data=data)

                is_valid = form.is_valid()

                assert not is_valid
                assert (
                    "School years may not have overlapping dates."
                    in form.non_field_errors()[0]
                )

    def test_school_year_overlap_with_itself(self):
        """A school year is permitted to overlap with itself when updating."""
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)

        data = {
            "school": str(school.id),
            "start_date": str(school_year.start_date - datetime.timedelta(days=1)),
            "end_date": str(school_year.end_date),
            "monday": True,
        }
        form = SchoolYearForm(user=school.admin, instance=school_year, data=data)

        is_valid = form.is_valid()

        assert is_valid

    def test_validate_one_week_day(self):
        """A school year must run on at least one day per week."""
        school = SchoolFactory()
        data = {
            "school": str(school.id),
            "start_date": "9/1/2020",
            "end_date": "6/1/2021",
        }
        form = SchoolYearForm(user=school.admin, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert (
            "A school year must run on at least one week day."
            in form.non_field_errors()
        )

    def test_max_length(self):
        """A school year has a maximum allowed length."""
        school = SchoolFactory()
        data = {
            "school": str(school.id),
            "start_date": "1/1/2020",
            "end_date": "12/31/2022",
            "monday": True,
        }
        form = SchoolYearForm(user=school.admin, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert (
            "A school year may not be longer than 500 days." in form.non_field_errors()
        )

    def test_school_year_days_superset_of_courses_days(self):
        """The days of a school year must be a superset of each course's days."""
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(
            grade_levels=[grade_level], days_of_week=Course.MONDAY + Course.TUESDAY
        )
        data = {
            "school": str(school.id),
            "start_date": "1/1/2020",
            "end_date": "12/31/2020",
            "monday": True,
        }
        form = SchoolYearForm(user=school.admin, instance=school_year, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert (
            "The school year days must include any days that a course runs."
            " The following courses run on more days than the school year:"
            f" {course}" in form.non_field_errors()
        )

    def test_no_date_change_with_breaks(self):
        """A school year must contain any breaks."""
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)
        start = school_year.start_date
        end = school_year.end_date
        SchoolBreakFactory(school_year=school_year, start_date=start, end_date=start)
        SchoolBreakFactory(school_year=school_year, start_date=end, end_date=end)
        data = {
            "school": str(school.id),
            "start_date": str(start + datetime.timedelta(days=1)),
            "end_date": str(end - datetime.timedelta(days=1)),
            "monday": True,
        }
        form = SchoolYearForm(user=school.admin, instance=school_year, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        errors = form.non_field_errors()
        assert "You have a school break before the school year's start date." in errors
        assert "You have a school break after the school year's end date." in errors


class TestSchoolBreakForm(TestCase):
    def test_create(self):
        """A school break is created."""
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)
        data = {
            "school_year": str(school_year.id),
            "start_date": str(school_year.start_date),
            "end_date": str(school_year.start_date),
        }
        form = SchoolBreakForm(user=school.admin, data=data)
        is_valid = form.is_valid()

        form.save()

        assert is_valid
        assert school_year.breaks.count() == 1

    def test_start_before_end(self):
        """The start date must be before the end date."""
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)
        data = {
            "school_year": str(school_year.id),
            "start_date": str(school_year.end_date + datetime.timedelta(days=3)),
            "end_date": str(school_year.start_date),
        }
        form = SchoolBreakForm(user=school.admin, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "The start date must be before the end date." in form.non_field_errors()

    def test_no_overlapping_breaks(self):
        """Two school breaks may not overlap."""
        school = SchoolFactory()
        school_break = SchoolBreakFactory(school_year__school=school)
        cases = [
            (
                "surround",
                str(school_break.start_date - datetime.timedelta(days=1)),
                str(school_break.end_date + datetime.timedelta(days=1)),
            ),
            (
                "inside",
                str(school_break.start_date + datetime.timedelta(days=1)),
                str(school_break.end_date - datetime.timedelta(days=1)),
            ),
            (
                "overlap_start",
                str(school_break.start_date - datetime.timedelta(days=1)),
                str(school_break.end_date - datetime.timedelta(days=1)),
            ),
            (
                "overlap_end",
                str(school_break.start_date + datetime.timedelta(days=1)),
                str(school_break.end_date + datetime.timedelta(days=1)),
            ),
        ]

        for case in cases:
            with self.subTest(case[0]):
                data = {
                    "school_year": str(school_break.school_year.id),
                    "start_date": case[1],
                    "end_date": case[2],
                }
                form = SchoolBreakForm(user=school.admin, data=data)

                is_valid = form.is_valid()

                assert not is_valid
                assert (
                    "School breaks may not have overlapping dates."
                    in form.non_field_errors()[0]
                )

    def test_school_break_overlap_with_itself(self):
        """A school break is permitted to overlap with itself when updating."""
        school = SchoolFactory()
        school_break = SchoolBreakFactory(school_year__school=school)
        data = {
            "school_year": str(school_break.school_year.id),
            "start_date": str(school_break.start_date - datetime.timedelta(days=1)),
            "end_date": str(school_break.end_date),
        }
        form = SchoolBreakForm(user=school.admin, instance=school_break, data=data)

        is_valid = form.is_valid()

        assert is_valid

    def test_break_in_school_year(self):
        """The school break must fit in the school year."""
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)
        cases = [
            (
                "before",
                str(school_year.start_date - datetime.timedelta(days=1)),
                str(school_year.start_date + datetime.timedelta(days=1)),
            ),
            (
                "after",
                str(school_year.end_date - datetime.timedelta(days=1)),
                str(school_year.end_date + datetime.timedelta(days=1)),
            ),
        ]
        for case in cases:
            with self.subTest(case[0]):
                data = {
                    "school_year": str(school_year.id),
                    "start_date": case[1],
                    "end_date": case[2],
                }
                form = SchoolBreakForm(user=school.admin, data=data)

                is_valid = form.is_valid()

                assert not is_valid
                assert (
                    "A break must be in the school year." in form.non_field_errors()[0]
                )

    def test_school_break_create_applies_to_one_student(self):
        """A school break is specific to a single student."""
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)
        enrollment = EnrollmentFactory(grade_level__school_year=school_year)
        EnrollmentFactory(grade_level__school_year=school_year)
        data = {
            "school_year": str(school_year.id),
            "start_date": str(school_year.start_date),
            "end_date": str(school_year.start_date),
            f"student-{enrollment.student.id}": str(enrollment.student.id),
        }
        form = SchoolBreakForm(user=school.admin, data=data)
        form.is_valid()

        form.save()

        school_break = school_year.breaks.first()
        student_on_break = school_break.students.first()
        assert enrollment.student == student_on_break

    def test_school_break_edit_clears_m2m(self):
        """A school break will clear m2m students if all students are on break."""
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)
        enrollment_1 = EnrollmentFactory(grade_level__school_year=school_year)
        enrollment_2 = EnrollmentFactory(grade_level__school_year=school_year)
        start = school_year.start_date
        school_break = SchoolBreakFactory(
            school_year=school_year, start_date=start, end_date=start
        )
        school_break.students.add(enrollment_1.student)
        data = {
            "school_year": str(school_year.id),
            "start_date": str(start),
            "end_date": str(start),
            f"student-{enrollment_1.student.id}": str(enrollment_1.student.id),
            f"student-{enrollment_2.student.id}": str(enrollment_2.student.id),
        }
        form = SchoolBreakForm(user=school.admin, instance=school_break, data=data)
        form.is_valid()

        form.save()

        assert school_break.students.count() == 0

    def test_school_break_edit_switches_student_break(self):
        """A school break will switch student who is on break."""
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)
        enrollment_1 = EnrollmentFactory(grade_level__school_year=school_year)
        enrollment_2 = EnrollmentFactory(grade_level__school_year=school_year)
        start = school_year.start_date
        school_break = SchoolBreakFactory(
            school_year=school_year, start_date=start, end_date=start
        )
        school_break.students.add(enrollment_1.student)
        data = {
            "school_year": str(school_year.id),
            "start_date": str(start),
            "end_date": str(start),
            f"student-{enrollment_2.student.id}": str(enrollment_2.student.id),
        }
        form = SchoolBreakForm(user=school.admin, instance=school_break, data=data)
        form.is_valid()

        form.save()

        assert school_break.students.first() == enrollment_2.student

    def test_at_least_one_enrolled(self):
        """When students are enrolled, at least one must be on a break."""
        school = SchoolFactory()
        school_break = SchoolBreakFactory(school_year__school=school)
        enrollment = EnrollmentFactory(
            grade_level__school_year=school_break.school_year
        )
        school_break.students.add(enrollment.student)
        EnrollmentFactory(grade_level=enrollment.grade_level)
        data = {
            "school_year": str(school_break.school_year.id),
            "start_date": str(school_break.start_date),
            "end_date": str(school_break.end_date),
        }
        form = SchoolBreakForm(user=school.admin, instance=school_break, data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "At least one student must be on break." in form.non_field_errors()[0]
