from django import forms

from .models import Course, CourseTask, GradedWork


class CourseForm(forms.ModelForm):
    monday = forms.BooleanField(required=False)
    tuesday = forms.BooleanField(required=False)
    wednesday = forms.BooleanField(required=False)
    thursday = forms.BooleanField(required=False)
    friday = forms.BooleanField(required=False)
    saturday = forms.BooleanField(required=False)
    sunday = forms.BooleanField(required=False)

    class Meta:
        model = Course
        fields = [
            "name",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]

    def save(self, *args, **kwargs):
        """Save the course and the days of week."""
        days_of_week = 0
        day_to_course_day = {
            "monday": Course.MONDAY,
            "tuesday": Course.TUESDAY,
            "wednesday": Course.WEDNESDAY,
            "thursday": Course.THURSDAY,
            "friday": Course.FRIDAY,
            "saturday": Course.SATURDAY,
            "sunday": Course.SUNDAY,
        }
        for day, course_day in day_to_course_day.items():
            if self.cleaned_data.get(day):
                days_of_week += course_day
        self.instance.days_of_week = days_of_week
        return super().save(*args, **kwargs)


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
