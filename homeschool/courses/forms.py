from django import forms

from .models import CourseTask, GradedWork


class IsGradedMixin(forms.Form):
    """Check if the task is graded.

    Course task creation and editing both need to check for graded work.
    Since they have different fields, this is added as a mixin.
    """

    is_graded = forms.BooleanField(required=False)

    def save(self, *args, **kwargs):
        task = super().save(*args, **kwargs)
        if self.cleaned_data["is_graded"]:
            if not task.graded_work:
                task.graded_work = GradedWork.objects.create()
                task.save()
        elif task.graded_work:
            task.graded_work.delete()
        return task


class CourseTaskCreateForm(IsGradedMixin, forms.ModelForm):
    class Meta:
        model = CourseTask
        fields = ["course", "description", "duration", "is_graded"]


class CourseTaskUpdateForm(IsGradedMixin, forms.ModelForm):
    class Meta:
        model = CourseTask
        fields = ["description", "duration", "is_graded"]
