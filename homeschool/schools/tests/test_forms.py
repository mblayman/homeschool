import datetime

from homeschool.schools.forms import SchoolBreakForm, SchoolYearForm
from homeschool.schools.tests.factories import (
    SchoolBreakFactory,
    SchoolFactory,
    SchoolYearFactory,
)
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


class TestSchoolBreakForm(TestCase):
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
