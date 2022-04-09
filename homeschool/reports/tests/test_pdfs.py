import io
import zipfile

from homeschool.reports import pdfs
from homeschool.schools.tests.factories import SchoolYearFactory
from homeschool.students.tests.factories import EnrollmentFactory
from homeschool.test import TestCase


class TestMakeBundle(TestCase):
    def test_happy(self):
        """The PDFs generate without error and produce a valid zip archive."""
        school_year = SchoolYearFactory()
        EnrollmentFactory(grade_level__school_year=school_year)

        zip_data = pdfs.make_bundle(school_year)

        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
            assert zip_file.testzip() is None
