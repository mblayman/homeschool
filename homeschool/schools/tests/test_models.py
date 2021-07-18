import datetime

from dateutil.relativedelta import MO, SU, relativedelta
from django.utils import timezone

from homeschool.core.schedules import Week
from homeschool.courses.tests.factories import CourseFactory, CourseTaskFactory
from homeschool.schools.models import SchoolBreak, SchoolYear
from homeschool.schools.tests.factories import (
    GradeLevelFactory,
    SchoolBreakFactory,
    SchoolFactory,
    SchoolYearFactory,
)
from homeschool.students.tests.factories import StudentFactory
from homeschool.test import TestCase


class TestSchool(TestCase):
    def test_factory(self):
        school = SchoolFactory()

        assert school is not None

    def test_has_admin(self):
        user = self.make_user()
        school = SchoolFactory(admin=user)

        assert school.admin == user

    def test_has_students(self):
        school = SchoolFactory()
        student = StudentFactory(school=school)

        assert list(school.students.all()) == [student]

    def test_str(self):
        school = SchoolFactory()

        assert school.admin.email in str(school)


class TestSchoolYear(TestCase):
    def test_factory(self):
        school_year = SchoolYearFactory()

        assert school_year is not None
        assert school_year.start_date is not None
        assert school_year.end_date is not None

    def test_str(self):
        same_year_start_date = datetime.date(2020, 1, 1)
        same_year_end_date = datetime.date(2020, 12, 31)
        same_year_school_year = SchoolYearFactory(
            start_date=same_year_start_date, end_date=same_year_end_date
        )
        academic_year_start_date = datetime.date(2020, 9, 1)
        academic_year_end_date = datetime.date(2021, 6, 15)
        academic_year_school_year = SchoolYearFactory(
            start_date=academic_year_start_date, end_date=academic_year_end_date
        )

        assert str(same_year_school_year) == "2020"
        assert str(academic_year_school_year) == "2020–2021"

    def test_has_school(self):
        school = SchoolFactory()
        school_year = SchoolYearFactory(school=school)

        assert school_year.school == school

    def test_has_days_of_week(self):
        days_of_week = SchoolYear.MONDAY + SchoolYear.TUESDAY
        school_year = SchoolYearFactory(days_of_week=days_of_week)

        assert school_year.days_of_week == days_of_week

    def test_has_grade_levels(self):
        school_year = SchoolYearFactory()
        grade_level = GradeLevelFactory(school_year=school_year)

        assert list(school_year.grade_levels.all()) == [grade_level]

    def test_runs_on(self):
        school_year = SchoolYearFactory(days_of_week=SchoolYear.MONDAY)

        assert school_year.runs_on(SchoolYear.MONDAY)
        assert not school_year.runs_on(SchoolYear.TUESDAY)

    def test_runs_on_date(self):
        school_year = SchoolYearFactory(days_of_week=SchoolYear.MONDAY)
        monday = datetime.date(2020, 1, 20)
        tuesday = datetime.date(2020, 1, 21)

        assert school_year.runs_on(monday)
        assert not school_year.runs_on(tuesday)

    def test_get_previous_day_from(self):
        school_year = SchoolYearFactory(days_of_week=SchoolYear.MONDAY)
        monday = datetime.date(2020, 1, 20)
        previous_monday = datetime.date(2020, 1, 13)

        assert school_year.get_previous_day_from(monday) == previous_monday

    def test_get_previous_day_from_no_running_days(self):
        school_year = SchoolYearFactory(days_of_week=0)
        monday = datetime.date(2020, 1, 20)

        assert school_year.get_previous_day_from(monday) == monday

    def test_get_next_day_from(self):
        school_year = SchoolYearFactory(days_of_week=SchoolYear.MONDAY)
        monday = datetime.date(2020, 1, 20)
        next_monday = datetime.date(2020, 1, 27)

        assert school_year.get_next_day_from(monday) == next_monday

    def test_get_next_day_from_no_running_days(self):
        school_year = SchoolYearFactory(days_of_week=0)
        monday = datetime.date(2020, 1, 20)

        assert school_year.get_next_day_from(monday) == monday

    def test_days_of_week_default(self):
        school_year = SchoolYearFactory()

        assert school_year.runs_on(SchoolYear.MONDAY)
        assert school_year.runs_on(SchoolYear.TUESDAY)
        assert school_year.runs_on(SchoolYear.WEDNESDAY)
        assert school_year.runs_on(SchoolYear.THURSDAY)
        assert school_year.runs_on(SchoolYear.FRIDAY)
        assert not school_year.runs_on(SchoolYear.SATURDAY)
        assert not school_year.runs_on(SchoolYear.SUNDAY)

    def test_get_week_dates_for(self):
        school_year = SchoolYearFactory()
        week = Week(datetime.date(2020, 1, 20))

        assert school_year.get_week_dates_for(week) == [
            datetime.date(2020, 1, 20),
            datetime.date(2020, 1, 21),
            datetime.date(2020, 1, 22),
            datetime.date(2020, 1, 23),
            datetime.date(2020, 1, 24),
        ]

    def test_last_school_day_for_week(self):
        school_year = SchoolYearFactory()
        monday = datetime.date.today() + relativedelta(weekday=MO(-1))
        friday = monday + datetime.timedelta(days=4)
        week = Week(monday)

        last_school_day = school_year.last_school_day_for(week)

        assert last_school_day == friday

    def test_last_school_day_for_no_days(self):
        school_year = SchoolYearFactory(days_of_week=SchoolYear.NO_DAYS)
        sunday = datetime.date.today() + relativedelta(weekday=SU(-1))
        week = Week(sunday)

        last_school_day = school_year.last_school_day_for(week)

        assert last_school_day == sunday

    def test_display_days(self):
        school_year = SchoolYearFactory.build(days_of_week=SchoolYear.ALL_DAYS)
        assert (
            school_year.display_days
            == "Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, and Saturday"
        )

        school_year.days_of_week = SchoolYear.MONDAY + SchoolYear.TUESDAY
        assert school_year.display_days == "Monday and Tuesday"

        school_year.days_of_week = SchoolYear.MONDAY
        assert school_year.display_days == "Monday"

        school_year.days_of_week = SchoolYear.NO_DAYS
        assert school_year.display_days == ""

    def test_display_days_abbreviated(self):
        school_year = SchoolYearFactory.build(days_of_week=SchoolYear.ALL_DAYS)

        assert school_year.display_abbreviated_days == "SuMTWRFSa"

    def test_display_days_abbreviated_no_days(self):
        school_year = SchoolYearFactory.build(days_of_week=SchoolYear.NO_DAYS)

        assert school_year.display_abbreviated_days == "Not Running"

    def test_has_school_break(self):
        """A date can return an existing school break."""
        expected_school_break = SchoolBreakFactory()
        school_year = expected_school_break.school_year

        school_break = school_year.get_break(expected_school_break.start_date)

        assert school_break == expected_school_break

    def test_no_school_break(self):
        """A data with no break is a null result."""
        school_year = SchoolYearFactory()

        school_break = school_year.get_break(school_year.start_date)

        assert school_break is None

    def test_is_break(self):
        """A school year can check if a date is a break day."""
        school_break = SchoolBreakFactory()
        school_year = school_break.school_year

        assert school_year.is_break(school_break.start_date)
        assert not school_year.is_break(
            school_break.end_date + datetime.timedelta(days=1)
        )

    def test_start_after_end(self):
        school_year = SchoolYearFactory()
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(grade_levels=[grade_level])
        start_date = datetime.date(2020, 5, 7)
        end_date = datetime.date(2020, 5, 5)

        count = school_year.get_task_count_in_range(course, start_date, end_date)

        assert count == 1

    def test_breaks_in_task_count(self):
        """A break is factored into the course task count."""
        school_year = SchoolYearFactory(days_of_week=SchoolYear.ALL_DAYS)
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(
            grade_levels=[grade_level], days_of_week=SchoolYear.ALL_DAYS
        )
        SchoolBreakFactory(
            school_year=school_year,
            start_date=school_year.start_date,
            end_date=school_year.start_date,
        )
        CourseTaskFactory(course=course)
        CourseTaskFactory(course=course)

        count = school_year.get_task_count_in_range(
            course,
            school_year.start_date,
            school_year.start_date + datetime.timedelta(days=1),
        )

        assert count == 1

    def test_next_course_day_with_break(self):
        """A break affects when the next course day is."""
        school_year = SchoolYearFactory(days_of_week=SchoolYear.ALL_DAYS)
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(
            grade_levels=[grade_level], days_of_week=SchoolYear.ALL_DAYS
        )
        SchoolBreakFactory(
            school_year=school_year,
            start_date=school_year.start_date + datetime.timedelta(days=1),
            end_date=school_year.start_date + datetime.timedelta(days=1),
        )

        next_course_day = school_year.get_next_course_day(
            course, school_year.start_date
        )

        assert next_course_day == school_year.start_date + datetime.timedelta(days=2)

    def test_next_course_day_all_breaks(self):
        """When all school days are breaks, get the last possible course day."""
        school_year = SchoolYearFactory(days_of_week=SchoolYear.ALL_DAYS)
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(
            grade_levels=[grade_level], days_of_week=SchoolYear.ALL_DAYS
        )
        SchoolBreakFactory(
            school_year=school_year,
            start_date=school_year.start_date,
            end_date=school_year.end_date,
        )

        next_course_day = school_year.get_next_course_day(
            course, school_year.start_date
        )

        assert next_course_day == school_year.end_date

    def test_next_course_day_course_not_running(self):
        """When the course isn't running, a next course day is returned."""
        school_year = SchoolYearFactory(days_of_week=SchoolYear.ALL_DAYS)
        grade_level = GradeLevelFactory(school_year=school_year)
        course = CourseFactory(
            grade_levels=[grade_level], days_of_week=SchoolYear.NO_DAYS
        )

        next_course_day = school_year.get_next_course_day(
            course, school_year.start_date
        )

        assert next_course_day == school_year.start_date


class TestGradeLevel(TestCase):
    def test_factory(self):
        grade_level = GradeLevelFactory()

        assert grade_level is not None
        assert grade_level.name != ""

    def test_str(self):
        grade_level = GradeLevelFactory()

        assert str(grade_level) == grade_level.name

    def test_has_name(self):
        name = "Kindergarten"
        grade_level = GradeLevelFactory(name=name)

        assert grade_level.name == name

    def test_has_school_year(self):
        school_year = SchoolYearFactory()
        grade_level = GradeLevelFactory(school_year=school_year)

        assert grade_level.school_year == school_year

    def test_has_courses(self):
        grade_level = GradeLevelFactory()
        course = CourseFactory()
        grade_level.courses.add(course)

        assert list(grade_level.courses.all()) == [course]

    def test_get_active_course(self):
        """The grade level can get its active courses."""
        grade_level = GradeLevelFactory()
        course = CourseFactory(grade_levels=[grade_level])
        CourseFactory(grade_levels=[grade_level], is_active=False)

        courses = grade_level.get_active_courses()

        assert courses == [course]


class TestSchoolBreak(TestCase):
    def test_factory(self):
        school_break = SchoolBreakFactory()

        assert school_break.start_date is not None
        assert school_break.end_date is not None
        assert school_break.description != ""
        assert school_break.school_year is not None

    def test_str(self):
        school_break = SchoolBreakFactory()

        assert str(school_break) == f"School Break {school_break.start_date}"

    def test_get_date_type(self):
        """Each date type has a representation."""
        today = timezone.localdate()
        single = SchoolBreakFactory.build(start_date=today, end_date=today)
        multi_day = SchoolBreakFactory.build(
            start_date=today, end_date=today + datetime.timedelta(days=2)
        )

        assert single.get_date_type(today) == SchoolBreak.DateType.SINGLE
        assert multi_day.get_date_type(today) == SchoolBreak.DateType.START
        assert (
            multi_day.get_date_type(today + datetime.timedelta(days=1))
            == SchoolBreak.DateType.MIDDLE
        )
        assert multi_day.get_date_type(multi_day.end_date) == SchoolBreak.DateType.END
        assert (
            multi_day.get_date_type(today - datetime.timedelta(days=1))
            == SchoolBreak.DateType.NOT_A_BREAK
        )
