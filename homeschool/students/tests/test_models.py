import datetime
import uuid

from dateutil.relativedelta import MO, SA, relativedelta
from django.utils import timezone

from homeschool.core.schedules import Week
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolFactory,
    SchoolYearFactory,
)
from homeschool.students.models import Enrollment
from homeschool.students.tests.factories import (
    CourseworkFactory,
    EnrollmentFactory,
    GradeFactory,
    StudentFactory,
)
from homeschool.test import TestCase


class TestStudent(TestCase):
    def test_factory(self):
        student = StudentFactory()

        assert student is not None
        assert student.first_name != ""
        assert student.last_name != ""

    def test_has_school(self):
        school = SchoolFactory()
        student = StudentFactory(school=school)

        assert student.school == school

    def test_has_first_name(self):
        first_name = "James"
        student = StudentFactory(first_name=first_name)

        assert student.first_name == first_name

    def test_has_last_name(self):
        last_name = "Bond"
        student = StudentFactory(last_name=last_name)

        assert student.last_name == last_name

    def test_has_uuid(self):
        student_uuid = uuid.uuid4()
        student = StudentFactory(uuid=student_uuid)

        assert student.uuid == student_uuid

    def test_full_name(self):
        student = StudentFactory()

        assert student.full_name == f"{student.first_name} {student.last_name}"

    def test_str(self):
        student = StudentFactory()

        assert str(student) == student.full_name

    def test_get_courses(self):
        enrollment = EnrollmentFactory()
        student = enrollment.student
        school_year = enrollment.grade_level.school_year
        GradeLevelFactory(school_year=school_year)
        course = CourseFactory()
        course.grade_levels.add(enrollment.grade_level)

        courses = student.get_courses(school_year)

        assert list(courses) == [course]

    def test_week_schedule_no_tasks_end_of_week(self):
        """A student has no tasks to complete if the school week is over."""
        today = datetime.date(2020, 5, 23)  # A Saturday
        week = Week(today)
        enrollment = EnrollmentFactory(
            grade_level__school_year__start_date=today - datetime.timedelta(days=30)
        )
        student = enrollment.student
        school_year = enrollment.grade_level.school_year
        CourseTaskFactory(course__grade_levels=[enrollment.grade_level])

        week_schedule = student.get_week_schedule(school_year, today, week)

        assert "task" not in week_schedule["courses"][0]["days"][0]

    def test_week_schedule_future_after_school_week(self):
        """Looking at future weeks pulls in unfinished tasks after the school week.

        This is a corner case. When the school week is over (typically a weekend
        date like Saturday or Sunday), all unfinished task work should be
        "pulled forward" to the next school week.
        This will enable users to plan for the following week.
        """
        today = timezone.now().date()
        saturday = today + relativedelta(weekday=SA(1))
        next_week = Week(saturday + datetime.timedelta(days=2))
        enrollment = EnrollmentFactory()
        student = enrollment.student
        school_year = enrollment.grade_level.school_year
        task = CourseTaskFactory(course__grade_levels=[enrollment.grade_level])

        week_schedule = student.get_week_schedule(school_year, saturday, next_week)

        assert week_schedule["courses"][0]["days"][0]["task"] == task

    def test_get_week_coursework(self):
        today = timezone.now().date()
        week = Week(today)
        enrollment = EnrollmentFactory(
            grade_level__school_year__start_date=today - datetime.timedelta(days=30)
        )
        student = enrollment.student
        school_year = enrollment.grade_level.school_year
        GradeLevelFactory(school_year=school_year)
        course = CourseFactory()
        course.grade_levels.add(enrollment.grade_level)
        coursework_1 = CourseworkFactory(
            student=student, course_task__course=course, completed_date=week.monday
        )
        coursework_2 = CourseworkFactory(
            student=student, course_task__course=course, completed_date=week.monday
        )

        week_coursework = student.get_week_coursework(week)

        assert week_coursework == {
            course.id: {week.monday: [coursework_1, coursework_2]}
        }

    def test_get_day_coursework(self):
        today = timezone.now().date()
        monday = today + relativedelta(weekday=MO(-1))
        enrollment = EnrollmentFactory(
            grade_level__school_year__start_date=today - datetime.timedelta(days=30)
        )
        student = enrollment.student
        school_year = enrollment.grade_level.school_year
        GradeLevelFactory(school_year=school_year)
        course = CourseFactory()
        course.grade_levels.add(enrollment.grade_level)
        coursework_1 = CourseworkFactory(
            student=student, course_task__course=course, completed_date=monday
        )
        coursework_2 = CourseworkFactory(
            student=student, course_task__course=course, completed_date=monday
        )

        day_coursework = student.get_day_coursework(monday)

        assert day_coursework == {course.id: [coursework_1, coursework_2]}

    def test_get_tasks_enrolled(self):
        """A student enrolled in a course gets all the correct tasks for that course."""
        enrollment = EnrollmentFactory()
        course = CourseFactory(grade_levels=[enrollment.grade_level])
        general_task = CourseTaskFactory(course=course)
        grade_level_task = CourseTaskFactory(
            course=course, grade_level=enrollment.grade_level
        )
        CourseTaskFactory(course=course, grade_level=GradeLevelFactory())

        course_tasks = enrollment.student.get_tasks_for(course)

        assert list(course_tasks) == [general_task, grade_level_task]

    def test_get_tasks_unenrolled(self):
        """A student not enrolled in a course gets no tasks."""
        student = StudentFactory()
        course_task = CourseTaskFactory()

        course_tasks = student.get_tasks_for(course_task.course)

        assert list(course_tasks) == []


class TestEnrollment(TestCase):
    def test_factory(self):
        enrollment = EnrollmentFactory()

        assert enrollment is not None

    def test_has_student(self):
        student = StudentFactory()
        enrollment = EnrollmentFactory(student=student)

        assert enrollment.student == student

    def test_has_grade_level(self):
        grade_level = GradeLevelFactory()
        enrollment = EnrollmentFactory(grade_level=grade_level)

        assert enrollment.grade_level == grade_level

    def test_student_is_enrolled(self):
        """A student is tested for enrollment in a school year."""
        enrollment = EnrollmentFactory()

        is_enrolled = Enrollment.is_student_enrolled(
            enrollment.student, enrollment.grade_level.school_year
        )

        assert is_enrolled

    def test_student_is_not_enrolled(self):
        """A student is not in a given school year."""
        student = StudentFactory()
        school_year = SchoolYearFactory()

        is_enrolled = Enrollment.is_student_enrolled(student, school_year)

        assert not is_enrolled

    def test_is_student_enrolled_none_school_year(self):
        """When a school year is None, a student isn't enrollment."""
        student = StudentFactory()
        school_year = None

        is_enrolled = Enrollment.is_student_enrolled(student, school_year)

        assert not is_enrolled


class TestCoursework(TestCase):
    def test_factory(self):
        coursework = CourseworkFactory()

        assert coursework is not None

    def test_has_student(self):
        student = StudentFactory()
        coursework = CourseworkFactory(student=student)

        assert coursework.student == student

    def test_has_course_task(self):
        course_task = CourseTaskFactory()
        coursework = CourseworkFactory(course_task=course_task)

        assert coursework.course_task == course_task

    def test_completed_date(self):
        completed_date = datetime.date.today()
        coursework = CourseworkFactory(completed_date=completed_date)

        assert coursework.completed_date == completed_date


class TestGrade(TestCase):
    def test_factory(self):
        grade = GradeFactory()

        assert grade is not None

    def test_has_student(self):
        student = StudentFactory()
        grade = GradeFactory(student=student)

        assert grade.student == student

    def test_has_graded_work(self):
        graded_work = GradedWorkFactory()
        grade = GradeFactory(graded_work=graded_work)

        assert grade.graded_work == graded_work

    def test_has_uuid(self):
        grade_uuid = uuid.uuid4()
        grade = GradeFactory(uuid=grade_uuid)

        assert grade.uuid == grade_uuid

    def test_has_score(self):
        score = 99
        grade = GradeFactory(score=score)

        assert grade.score == score
