from typing import Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, TemplateView

from homeschool.courses.models import Course, GradedWork
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.students.models import Coursework, Enrollment, Grade, Student

from .exceptions import FullEnrollmentError, NoGradeLevelError, NoStudentError
from .forms import EnrollmentForm


class StudentIndexView(LoginRequiredMixin, TemplateView):
    template_name = "students/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_link"] = "students"

        user = self.request.user
        context["school_year"] = SchoolYear.get_current_year_for(user)
        context["roster"] = []
        for student in Student.objects.filter(school=user.school):
            context["roster"].append(
                {
                    "student": student,
                    "enrollment": Enrollment.objects.filter(
                        student=student, grade_level__school_year=context["school_year"]
                    )
                    .select_related("grade_level")
                    .first(),
                }
            )
        return context


class StudentCreateView(LoginRequiredMixin, CreateView):
    template_name = "students/student_form.html"
    model = Student
    fields = ("school", "first_name", "last_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        return context

    def get_success_url(self):
        return reverse("students:index")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if "data" in kwargs:
            data = kwargs["data"].copy()
            data["school"] = self.request.user.school
            kwargs["data"] = data
        return kwargs


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
            elif course_is_running:
                task_item["planned_date"] = next_course_day
                next_course_day = school_year.get_next_course_day(
                    course, next_course_day
                )
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
        context["has_work_to_grade"] = any(
            [
                student_work.get("graded_work")
                for student_work in context["work_to_grade"]
            ]
        )
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


class EnrollmentCreateView(LoginRequiredMixin, CreateView):
    template_name = "students/enrollment_form.html"
    form_class = EnrollmentForm

    def dispatch(self, *args, **kwargs):
        try:
            return super().dispatch(*args, **kwargs)
        except FullEnrollmentError:
            return HttpResponseRedirect(
                reverse(
                    "schools:school_year_detail", args=[self.kwargs["school_year_uuid"]]
                )
            )
        except NoGradeLevelError:
            return HttpResponseRedirect(
                reverse(
                    "schools:grade_level_create", args=[self.kwargs["school_year_uuid"]]
                )
            )
        except NoStudentError:
            return HttpResponseRedirect(reverse("students:index"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_year = get_object_or_404(
            SchoolYear,
            uuid=self.kwargs["school_year_uuid"],
            school__admin=self.request.user,
        )
        context["school_year"] = school_year
        context["grade_levels"] = self._get_grade_levels(school_year)
        context["students"] = self._get_students(school_year)
        return context

    def _get_grade_levels(self, school_year):
        grade_levels = GradeLevel.objects.filter(school_year=school_year)
        if not grade_levels:
            messages.add_message(
                self.request,
                messages.INFO,
                "You need to create a grade level for a student to enroll in.",
            )
            raise NoGradeLevelError()
        return grade_levels

    def _get_students(self, school_year):
        students = Student.objects.filter(school__admin=self.request.user)
        if not students:
            messages.add_message(
                self.request, messages.INFO, "You need to add a student to enroll."
            )
            raise NoStudentError()

        enrollments = Enrollment.objects.filter(
            grade_level__school_year=school_year
        ).select_related("student")
        if len(students) == len(enrollments):
            messages.add_message(
                self.request,
                messages.INFO,
                "All students are enrolled in the school year.",
            )
            raise FullEnrollmentError()
        enrolled_students = set(enrollment.student for enrollment in enrollments)
        return [student for student in students if student not in enrolled_students]

    def get_success_url(self):
        return reverse(
            "schools:school_year_detail", args=[self.kwargs["school_year_uuid"]]
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class StudentEnrollmentCreateView(LoginRequiredMixin, CreateView):
    """Enroll a student with a simplified form that only presents grade levels."""

    template_name = "students/student_enrollment_form.html"
    form_class = EnrollmentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_uuid = self.kwargs["uuid"]
        context["student"] = get_object_or_404(
            Student, uuid=student_uuid, school__admin=self.request.user
        )

        school_year_uuid = self.kwargs["school_year_uuid"]
        context["school_year"] = get_object_or_404(
            SchoolYear, uuid=school_year_uuid, school__admin=self.request.user
        )

        context["grade_levels"] = GradeLevel.objects.filter(
            school_year=context["school_year"]
        )
        return context

    def get_success_url(self):
        return reverse("students:index")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
