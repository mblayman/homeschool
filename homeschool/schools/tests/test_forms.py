import datetime

from homeschool.schools.forms import SchoolYearForm
from homeschool.schools.tests.factories import SchoolFactory, SchoolYearFactory
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
