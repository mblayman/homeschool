from django import forms

from homeschool.core.forms import DaysOfWeekModelForm
from homeschool.schools.models import GradeLevel

from .models import Course, CourseTask, GradedWork


class CourseForm(DaysOfWeekModelForm):
    class Meta:
        model = Course
        fields = ["name", "grade_levels"] + DaysOfWeekModelForm.days_of_week_fields

    grade_levels = forms.ModelMultipleChoiceField(queryset=GradeLevel.objects.none())

    def __init__(self, school_year, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Saving this to an attribute isn't really needed,
        # but it's useful for verification.
        self.school_year = school_year
        self.fields["grade_levels"].queryset = GradeLevel.objects.filter(
            school_year=school_year
        )


class CourseTaskForm(forms.ModelForm):
    class Meta:
        model = CourseTask
        fields = ["course", "description", "duration", "is_graded", "grade_level"]

    is_graded = forms.BooleanField(required=False)

    def save(self, *args, **kwargs):
        task = super().save(*args, **kwargs)
        if self.cleaned_data["is_graded"]:
            if not hasattr(task, "graded_work"):
                GradedWork.objects.create(course_task=task)
        elif hasattr(task, "graded_work"):
            task.graded_work.delete()
        return task
