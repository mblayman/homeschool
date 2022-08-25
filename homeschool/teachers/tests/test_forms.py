from homeschool.courses.tests.factories import CourseFactory
from homeschool.schools.tests.factories import GradeLevelFactory
from homeschool.teachers.forms import ChecklistForm
from homeschool.teachers.tests.factories import ChecklistFactory
from homeschool.test import TestCase


class TestChecklistForm(TestCase):
    def test_creates_checklist(self):
        """A checklist is created on save."""
        grade_level = GradeLevelFactory()
        course = CourseFactory(grade_levels=[grade_level])
        form = ChecklistForm({}, school_year=grade_level.school_year)

        form.save()

        assert grade_level.school_year.checklists.count() == 1
        checklist = grade_level.school_year.checklists.first()
        assert checklist.excluded_courses == [str(course.id)]

    def test_includes_course(self):
        """A course is included for display."""
        grade_level = GradeLevelFactory()
        course = CourseFactory(grade_levels=[grade_level])
        form = ChecklistForm(
            {f"course-{course.id}": "on"}, school_year=grade_level.school_year
        )

        form.save()

        checklist = grade_level.school_year.checklists.first()
        assert checklist.excluded_courses == []

    def test_updates_checklist(self):
        """An existing checklist is updated on save."""
        grade_level = GradeLevelFactory()
        checklist = ChecklistFactory(school_year=grade_level.school_year)
        course = CourseFactory(grade_levels=[grade_level])
        form = ChecklistForm({}, school_year=grade_level.school_year)

        form.save()

        checklist.refresh_from_db()
        assert checklist.excluded_courses == [str(course.id)]
