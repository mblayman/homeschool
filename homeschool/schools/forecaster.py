import datetime
from typing import Optional

from django.utils import timezone

from homeschool.courses.models import Course
from homeschool.students.models import Coursework, Student


class Forecaster:
    """For project dates about school years and courses"""

    def get_last_forecast_date(
        self, student: Student, course: Course
    ) -> Optional[datetime.date]:
        """Get the last forecast date of course for the student."""
        task_items = self.get_task_items(student, course)
        if not task_items:
            return None

        task_item = task_items[-1]
        if "planned_date" in task_item:
            return task_item["planned_date"]
        return task_item["coursework"].completed_date

    def get_task_items(self, student, course):
        today = timezone.localdate()

        # When the school year isn't in progress yet,
        # the offset calculations should come
        # relative to the start of the school year.
        school_year = course.school_year
        if today < school_year.start_date:
            today = school_year.start_date

        if not school_year.is_break(today) and course.runs_on(today):
            next_course_day = today
        else:
            next_course_day = school_year.get_next_course_day(course, today)

        course_is_running = course.is_running
        coursework_by_task = self._get_course_work_by_task(student, course)
        course_tasks = student.get_tasks_for(course).select_related("graded_work")
        task_items = []
        for course_task in course_tasks:
            task_item = {
                "course_task": course_task,
                "has_graded_work": hasattr(course_task, "graded_work"),
            }
            if course_task in coursework_by_task:
                coursework = coursework_by_task[course_task]
                # Advance the next course day to deconflict with coursework.
                if coursework.completed_date == next_course_day:
                    next_course_day = school_year.get_next_course_day(
                        course, next_course_day
                    )
                task_item["coursework"] = coursework
            elif course_is_running:
                task_item["planned_date"] = next_course_day
                next_course_day = school_year.get_next_course_day(
                    course, next_course_day
                )
            task_items.append(task_item)

        return task_items

    def _get_course_work_by_task(self, student, course):
        coursework = Coursework.objects.filter(
            student=student, course_task__course=course
        ).select_related("course_task")
        return {c.course_task: c for c in coursework}
