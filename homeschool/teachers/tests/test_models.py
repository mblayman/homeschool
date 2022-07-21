from homeschool.courses.tests.factories import CourseFactory
from homeschool.schools.tests.factories import GradeLevelFactory
from homeschool.teachers.models import Checklist
from homeschool.teachers.tests.factories import ChecklistFactory
from homeschool.test import TestCase


class TestChecklist(TestCase):
    def test_factory(self):
        checklist = ChecklistFactory()

        assert checklist is not None
        assert checklist.school_year is not None
        assert checklist.excluded_courses == []

    def test_course_exclude_from_schedule(self):
        """A checklist excludes a course from a weekly schedule."""
        grade_level = GradeLevelFactory()
        course = CourseFactory(grade_levels=[grade_level])
        ChecklistFactory(
            school_year=grade_level.school_year, excluded_courses=[str(course.id)]
        )
        schedules = [{"courses": [{"course": course}]}]

        Checklist.filter_schedules(grade_level.school_year, schedules)

        assert schedules == [{"courses": []}]
