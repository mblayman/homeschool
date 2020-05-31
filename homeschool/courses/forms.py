from django import forms

from homeschool.core.forms import DaysOfWeekModelForm

from .models import Course, CourseTask, GradedWork


class CourseForm(DaysOfWeekModelForm):
    class Meta:
        model = Course
        fields = ["name"] + DaysOfWeekModelForm.days_of_week_fields


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
