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

        return self.cleaned_data
