import datetime

import pytest
from dateutil.relativedelta import MO, SA, SU, relativedelta
from django.db import IntegrityError
from django.utils import timezone
from freezegun import freeze_time

from homeschool.core.schedules import Week
from homeschool.courses.models import Course
from homeschool.courses.tests.factories import (
    CourseFactory,
    CourseTaskFactory,
    GradedWorkFactory,
)
from homeschool.schools.models import SchoolYear
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolBreakFactory,
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

    def test_full_name(self):
        student = StudentFactory()

        assert student.full_name == f"{student.first_name} {student.last_name}"

    def test_str(self):
        student = StudentFactory()

        assert str(student) == student.full_name

    def test_get_active_courses(self):
        """Get the student's active courses."""
        enrollment = EnrollmentFactory()
        student = enrollment.student
        school_year = enrollment.grade_level.school_year
        GradeLevelFactory(school_year=school_year)
        course = CourseFactory()
        course.grade_levels.add(enrollment.grade_level)

        courses = student.get_active_courses(school_year)

        assert list(courses) == [course]

    def test_get_courses_no_enrollment(self):
        """An unenrolled student has no course for a school year."""
        student = StudentFactory()
        school_year = SchoolYearFactory()

        courses = student.get_active_courses(school_year)

        assert courses == []

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

    @pytest.mark.xfail(reason="Not implemented yet. See #433")
    @freeze_time("2021-07-21")  # Wednesday
    def test_get_week_with_breaks(self):
        """Next week starts with the correct task when the current week has breaks."""
        today = timezone.now().date()
        next_week = Week(today + datetime.timedelta(days=7))
        enrollment = EnrollmentFactory()
        school_year = enrollment.grade_level.school_year
        student = enrollment.student
        course = CourseFactory(grade_levels=[enrollment.grade_level])
        CourseworkFactory(
            student=student, course_task__course=course, completed_date=today
        )
        task = CourseTaskFactory(course=course)
        # TODO: remove wrong task
        CourseTaskFactory(course=course)
        SchoolBreakFactory(
            school_year=school_year,
            start_date=today + datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=2),
        )

        week_schedule = student.get_week_schedule(school_year, today, next_week)

        assert week_schedule["courses"][0]["days"][0]["task"] == task

    def test_week_schedule_future_after_school_week(self):
        """Looking at future weeks pulls in unfinished tasks after the school week.

        This is a corner case. When the school week is over (typically a weekend
        date like Saturday or Sunday), all unfinished task work should be
        "pulled forward" to the next school week.
        This will enable users to plan for the following week.
        """
        today = timezone.localdate()
        saturday = today + relativedelta(weekday=SA(1))
        next_week = Week(saturday + datetime.timedelta(days=2))
        enrollment = EnrollmentFactory()
        student = enrollment.student
        school_year = enrollment.grade_level.school_year
        task = CourseTaskFactory(course__grade_levels=[enrollment.grade_level])

        week_schedule = student.get_week_schedule(school_year, saturday, next_week)

        assert week_schedule["courses"][0]["days"][0]["task"] == task

    def test_week_schedule_tasks_after_last_coursework(self):
        """Remaining tasks should only appear after the last completed coursework."""
        today = timezone.localdate()
        sunday = today + relativedelta(weekday=SU(-1))
        week = Week(sunday)
        enrollment = EnrollmentFactory(
            grade_level__school_year__days_of_week=SchoolYear.ALL_DAYS
        )
        student = enrollment.student
        school_year = enrollment.grade_level.school_year
        completed_task = CourseTaskFactory(
            course__days_of_week=Course.ALL_DAYS,
            course__grade_levels=[enrollment.grade_level],
        )
        coursework = CourseworkFactory(
            student=student,
            course_task=completed_task,
            completed_date=sunday + datetime.timedelta(days=1),
        )
        to_do_task = CourseTaskFactory(course=completed_task.course)

        week_schedule = student.get_week_schedule(school_year, sunday, week)

        assert week_schedule["courses"][0]["days"][1]["coursework"] == [coursework]
        assert week_schedule["courses"][0]["days"][2]["task"] == to_do_task

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
            student=student, course_task__course=course, completed_date=week.first_day
        )
        coursework_2 = CourseworkFactory(
            student=student, course_task__course=course, completed_date=week.first_day
        )

        week_coursework = student.get_week_coursework(week)

        assert week_coursework == {
            course.id: {week.first_day: [coursework_1, coursework_2]}
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

    def test_get_incomplete_task_count_in_range(self):
        """The student can get the count of incomplete tasks for a course."""
        enrollment = EnrollmentFactory(
            grade_level__school_year__days_of_week=SchoolYear.ALL_DAYS
        )
        school_year = enrollment.grade_level.school_year
        student = enrollment.student
        course = CourseFactory(
            grade_levels=[enrollment.grade_level], days_of_week=Course.ALL_DAYS
        )
        coursework = CourseworkFactory(student=student, course_task__course=course)
        CourseTaskFactory(course=course)

        incomplete_task_count = student.get_incomplete_task_count_in_range(
            course,
            coursework.completed_date,
            coursework.completed_date + datetime.timedelta(days=1),
            school_year,
        )

        assert incomplete_task_count == 1


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

    def test_unique_student_per_grade_level(self):
        """A student enrollment is unique per grade level."""
        enrollment = EnrollmentFactory()

        with pytest.raises(IntegrityError):
            Enrollment.objects.create(
                student=enrollment.student, grade_level=enrollment.grade_level
            )


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

    def test_has_score(self):
        score = 99
        grade = GradeFactory(score=score)

        assert grade.score == score
