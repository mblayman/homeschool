from django import forms

from .models import Coursework, Enrollment, Grade


class EnrolledTaskMixin:
    """Can check if the student is enrolled in the course that has the task."""

    def _is_enrolled_task(self, student, course_task):
        """The student is permitted to complete the task."""
        if not Enrollment.objects.filter(
            student=student, grade_level__in=course_task.course.grade_levels.all()
        ).exists():
            raise forms.ValidationError("The student is not enrolled in this course.")


class CourseworkForm(EnrolledTaskMixin, forms.ModelForm):
    class Meta:
        model = Coursework
        fields = ["student", "course_task", "completed_date"]

    def clean(self):
        super().clean()
        student = self.cleaned_data.get("student")
        course_task = self.cleaned_data.get("course_task")
        completed_date = self.cleaned_data.get("completed_date")

        # Any of these being None is field level validation failure,
        # but a guard is needed to prevent unnecessary processing.
        if student is None or course_task is None or completed_date is None:
            return

        self._is_enrolled_task(student, course_task)
        self._check_completed_date_in_school_year(completed_date, course_task)
        return self.cleaned_data

    def _check_completed_date_in_school_year(self, completed_date, course_task):
        """The completed date must be in the school year."""
        grade_level = course_task.course.grade_levels.select_related(
            "school_year"
        ).first()
        if grade_level and not (
            grade_level.school_year.start_date
            <= completed_date
            <= grade_level.school_year.end_date
        ):
            raise forms.ValidationError(
                "The completed date must be in the school year."
            )

    def save(self):
        """Create or update a coursework."""
        Coursework.objects.update_or_create(
            student=self.cleaned_data["student"],
            course_task=self.cleaned_data["course_task"],
            defaults={"completed_date": self.cleaned_data["completed_date"]},
        )


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["student", "grade_level"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        student = self.cleaned_data.get("student")
        if student and student.school != self.user.school:
            raise forms.ValidationError("You may not enroll that student.")

        grade_level = self.cleaned_data.get("grade_level")
        if not grade_level:
            raise forms.ValidationError("You need to select a grade level.")

        if grade_level.school_year.school != self.user.school:
            raise forms.ValidationError("You may not enroll to that grade level.")

        enrollment = (
            Enrollment.objects.filter(
                student=student, grade_level__school_year=grade_level.school_year
            )
            .select_related("student", "grade_level")
            .first()
        )
        if enrollment:
            raise forms.ValidationError(
                "A student may not be enrolled in multiple grade levels in a school"
                f" year. {enrollment.student} is enrolled in {enrollment.grade_level}."
            )

        return self.cleaned_data


class GradeForm(EnrolledTaskMixin, forms.ModelForm):
    class Meta:
        model = Grade
        fields = ["student", "graded_work", "score"]

    def clean(self):
        super().clean()
        student = self.cleaned_data.get("student")
        graded_work = self.cleaned_data.get("graded_work")

        # Any of these being None is field level validation failure,
        # but a guard is needed to prevent unnecessary processing.
        if student is None or graded_work is None:
            return

        self._is_enrolled_task(student, graded_work.course_task)
        return self.cleaned_data

    def save(self):
        """Create or update a grade."""
        Grade.objects.update_or_create(
            student=self.cleaned_data["student"],
            graded_work=self.cleaned_data["graded_work"],
            defaults={"score": self.cleaned_data["score"]},
        )
