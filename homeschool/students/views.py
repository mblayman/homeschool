from typing import Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.utils import timezone
from django.views.generic.base import TemplateView

from homeschool.courses.models import Course, GradedWork
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.students.models import Coursework, Grade


class StudentIndexView(LoginRequiredMixin, TemplateView):
    template_name = "students/index.html"


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
        if not self.request.GET.get("completed_tasks"):
            context["task_items"] = [
                item for item in context["task_items"] if "coursework" not in item
            ]
        return context

    def get_student(self, user):
        return get_object_or_404(user.school.students.all(), uuid=self.kwargs["uuid"])

    def get_course(self, user):
        grade_levels = GradeLevel.objects.filter(school_year__school__admin=user)
        return get_object_or_404(
            Course.objects.filter(grade_levels__in=grade_levels).distinct(),
            uuid=self.kwargs["course_uuid"],
        )

    def get_task_items(self, student, course):
        today = timezone.now().date()
        if course.runs_on(today):
            next_course_day = today
        else:
            next_course_day = course.get_next_day_from(today)

        coursework_by_task = self.get_course_work_by_task(student, course)
        course_tasks = student.get_tasks_for(course).select_related("graded_work")
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

    def get_course_work_by_task(self, student, course):
        coursework = Coursework.objects.filter(
            student=student, course_task__course=course
        ).select_related("course_task")
        return {c.course_task: c for c in coursework}


class GradeView(LoginRequiredMixin, TemplateView):
    """Grade any graded work for a set a students."""

    template_name = "students/grade.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["work_to_grade"] = self.get_students_graded_work()
        return context

    def get_students_graded_work(self):
        """Get all the graded work for each student."""
        students = self.request.user.school.students.all()

        graded_work_by_student = []
        for student in students:
            graded_work_for_student = {
                "student": student,
                "graded_work": self.get_graded_work(student),
            }
            graded_work_by_student.append(graded_work_for_student)
        return graded_work_by_student

    def get_graded_work(self, student):
        today = self.request.user.get_local_today()
        school_year = SchoolYear.objects.filter(
            school=self.request.user.school, start_date__lte=today, end_date__gte=today
        ).first()
        if not school_year:
            return []

        grade_levels = GradeLevel.objects.filter(school_year=school_year)
        courses = Course.objects.filter(grade_levels__in=grade_levels)
        completed_task_ids = Coursework.objects.filter(
            student=student, course_task__course__in=courses
        ).values_list("course_task_id", flat=True)

        graded_work = GradedWork.objects.filter(
            course_task__in=completed_task_ids
        ).select_related("course_task", "course_task__course")

        already_graded_work_ids = set(
            Grade.objects.filter(
                student=student, graded_work__in=graded_work
            ).values_list("graded_work_id", flat=True)
        )
        return [work for work in graded_work if work.id not in already_graded_work_ids]

    def post(self, request, *args, **kwargs):
        self.persist_grades()
        success_url = request.GET.get("next", reverse("core:daily"))
        return HttpResponseRedirect(success_url)

    def persist_grades(self):
        """Parse the scores and persist new grades."""
        scores = self.get_scores()

        school = self.request.user.school
        grades = []
        students = self.request.user.school.students.filter(id__in=scores.keys())
        for student in students:
            grade_levels = GradeLevel.objects.filter(school_year__school=school)
            courses = Course.objects.filter(grade_levels__in=grade_levels)
            graded_work_ids = set(
                GradedWork.objects.filter(
                    id__in=scores[student.id].keys(), course_task__course__in=courses
                ).values_list("id", flat=True)
            )
            already_graded_work_ids = set(
                Grade.objects.filter(
                    student=student, graded_work__in=graded_work_ids
                ).values_list("graded_work_id", flat=True)
            )
            graded_work_missing_grades = graded_work_ids - already_graded_work_ids
            for graded_work_id in graded_work_missing_grades:
                grades.append(
                    Grade(
                        student=student,
                        graded_work_id=graded_work_id,
                        score=int(scores[student.id][graded_work_id]),
                    )
                )

        if grades:
            grades_created = len(Grade.objects.bulk_create(grades))
            message = "Saved {} grade{}.".format(
                grades_created, pluralize(grades_created)
            )
            messages.add_message(self.request, messages.SUCCESS, message)

    def get_scores(self):
        raw_scores = {
            k: v for k, v in self.request.POST.items() if k.startswith("graded_work")
        }
        scores: Dict[int, Dict[int, str]] = {}
        for student_work, score in raw_scores.items():
            if not score:
                continue
            work_parts = student_work.split("-")
            student_id = int(work_parts[1])
            graded_work_id = int(work_parts[2])
            if student_id not in scores:
                scores[student_id] = {}
            scores[student_id][graded_work_id] = score

        return scores
