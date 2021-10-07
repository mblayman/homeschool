from django import forms

from homeschool.core.forms import DaysOfWeekModelForm
from homeschool.schools.models import GradeLevel

from .models import Course, CourseResource, CourseTask, GradedWork


class CourseForm(DaysOfWeekModelForm):
    class Meta:
        model = Course
        fields = [
            "name",
            "default_task_duration",
            "grade_levels",
            "is_active",
        ] + DaysOfWeekModelForm.days_of_week_fields
        labels = {"is_active": "Is Active?"}

    grade_levels = forms.ModelMultipleChoiceField(queryset=GradeLevel.objects.none())

    def __init__(self, school_year, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Saving this to an attribute isn't really needed,
        # but it's useful for verification.
        self.school_year = school_year
        self.fields["grade_levels"].queryset = GradeLevel.objects.filter(
            school_year=school_year
        )

    def clean(self):
        if not self.school_year:
            raise forms.ValidationError("A school year is missing.")

        if not self.school_year.is_superset(self.get_days_of_week()):
            raise forms.ValidationError(
                "The course must run within school year days:"
                f" {self.school_year.display_days}"
            )
        return self.cleaned_data


class CourseResourceForm(forms.ModelForm):
    class Meta:
        model = CourseResource
        fields = ["course", "title", "details"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        course = self.cleaned_data.get("course")
        if not course:
            raise forms.ValidationError("Invalid course.")

        if not course.belongs_to(self.user):
            raise forms.ValidationError(
                "You may not add a resource to another user's course."
            )
        return self.cleaned_data


class CourseTaskBulkDeleteForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        """Ensure the tasks IDs only apply to the user's school."""
        task_ids = [id_ for key, id_ in self.data.items() if key.startswith("task-")]

        grade_levels = GradeLevel.objects.filter(
            school_year__school__admin=self.user
        ).values_list("id", flat=True)
        users_deletable_tasks = CourseTask.objects.filter(
            course__grade_levels__in=grade_levels, id__in=task_ids
        )
        if len(task_ids) != users_deletable_tasks.count():
            raise forms.ValidationError(
                "Sorry, you do not have permission to delete the selected tasks."
            )

        return self.cleaned_data

    def save(self):
        """Delete the selected tasks."""
        task_ids = [id_ for key, id_ in self.data.items() if key.startswith("task-")]
        _, deleted_info = CourseTask.objects.filter(id__in=task_ids).delete()
        return deleted_info["courses.CourseTask"]


class CourseTaskForm(forms.ModelForm):
    class Meta:
        model = CourseTask
        fields = ["course", "description", "duration", "is_graded", "grade_level"]

    is_graded = forms.BooleanField(required=False, label="Is graded?")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        course = self.cleaned_data.get("course")
        if not course:
            raise forms.ValidationError("Invalid course.")

        if not course.belongs_to(self.user):
            raise forms.ValidationError(
                "You may not add a task to another user's course."
            )
        return self.cleaned_data

    def save(self, *args, **kwargs):
        task = super().save(*args, **kwargs)
        if self.cleaned_data["is_graded"]:
            if not hasattr(task, "graded_work"):
                GradedWork.objects.create(course_task=task)
        elif hasattr(task, "graded_work"):
            task.graded_work.delete()
        return task
