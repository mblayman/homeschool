from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic.base import TemplateView

from homeschool.courses.models import Course
from homeschool.students.models import Coursework


class StudentCourseView(LoginRequiredMixin, TemplateView):
    template_name = "students/course.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user = self.request.user
        context["student"] = self.get_student(user)
        context["course"] = self.get_course(user)
        context["task_items"] = self.get_task_items(
            context["student"], context["course"]
        )
        return context

    def get_student(self, user):
        return get_object_or_404(user.school.students.all(), uuid=self.kwargs["uuid"])

    def get_course(self, user):
        return get_object_or_404(
            Course.objects.filter(
                grade_level__school_year__school__admin=user
            ).select_related("grade_level"),
            uuid=self.kwargs["course_uuid"],
        )

    def get_course_work_by_task(self, student, course):
        coursework = Coursework.objects.filter(
            student=student, course_task__course=course
        ).select_related("course_task")
        return {c.course_task: c for c in coursework}

    def get_task_items(self, student, course):
        today = timezone.now().date()
        if course.runs_on(today):
            next_course_day = today
        else:
            next_course_day = course.get_next_day_from(today)

        coursework_by_task = self.get_course_work_by_task(student, course)

        course_tasks = course.course_tasks.all().select_related("graded_work")
        task_items = []
        for course_task in course_tasks:
            task_item = {
                "course_task": course_task,
                "has_graded_work": hasattr(course_task, "graded_work"),
            }
            if course_task in coursework_by_task:
                task_item["coursework"] = coursework_by_task[course_task]
            else:
                task_item["planned_date"] = next_course_day
                next_course_day = course.get_next_day_from(next_course_day)
            task_items.append(task_item)

        return task_items
