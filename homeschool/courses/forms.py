from django import forms

from .models import CourseTask, GradedWork


class CourseTaskForm(forms.ModelForm):
    class Meta:
        model = CourseTask
        fields = ["course", "description", "duration", "is_graded"]

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
