from homeschool.reports.contexts import CourseworkReportContext
from homeschool.students.tests.factories import CourseworkFactory, EnrollmentFactory
from homeschool.test import TestCase


class TestCourseworkReportContext(TestCase):
    def test_course_has_tasks(self):
        """The courses have coursework tasks annotated to each course."""
        enrollment = EnrollmentFactory()
        coursework = CourseworkFactory(
            student=enrollment.student,
            course_task__course__grade_levels=[enrollment.grade_level],
        )
        course = coursework.course_task.course

        context = CourseworkReportContext.from_enrollment(enrollment)

        expected_tasks = [(coursework.course_task, coursework)]
        course.tasks = expected_tasks
        assert context.courses == [course]
