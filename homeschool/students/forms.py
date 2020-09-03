from django import forms

from .models import Enrollment


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
        if grade_level and grade_level.school_year.school != self.user.school:
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
