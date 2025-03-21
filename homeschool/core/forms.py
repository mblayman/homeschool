from django import forms

from .models import DaysOfWeekModel


class DaysOfWeekModelForm(forms.ModelForm):
    """A form to handle a DaysOfWeekModel.

    Sub-classing forms must define their own Meta
    and extend `fields` with days_of_week_fields.
    """

    sunday = forms.BooleanField(required=False)
    monday = forms.BooleanField(required=False)
    tuesday = forms.BooleanField(required=False)
    wednesday = forms.BooleanField(required=False)
    thursday = forms.BooleanField(required=False)
    friday = forms.BooleanField(required=False)
    saturday = forms.BooleanField(required=False)

    days_of_week_fields = [
        "sunday",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
    ]
    day_field_to_model_day = {
        "sunday": DaysOfWeekModel.SUNDAY,
        "monday": DaysOfWeekModel.MONDAY,
        "tuesday": DaysOfWeekModel.TUESDAY,
        "wednesday": DaysOfWeekModel.WEDNESDAY,
        "thursday": DaysOfWeekModel.THURSDAY,
        "friday": DaysOfWeekModel.FRIDAY,
        "saturday": DaysOfWeekModel.SATURDAY,
    }

    def save(self, *args, **kwargs):
        """Save the model instance and the days of week."""
        self.instance.days_of_week = self.get_days_of_week()
        return super().save(*args, **kwargs)

    def get_days_of_week(self):
        """Get the days of week from the cleaned data."""
        days_of_week = 0
        for day_field, model_day in self.day_field_to_model_day.items():
            if self.cleaned_data.get(day_field):
                days_of_week += model_day
        return days_of_week


class OnboardingForm(forms.Form):
    student_first_name = forms.CharField(label="First Name", max_length=64)
    student_last_name = forms.CharField(label="Last Name", max_length=64)
    school_year_start_date = forms.DateField(label="Start Date")
    school_year_end_date = forms.DateField(label="End Date")
    grade_level_name = forms.CharField(label="Grade Level", max_length=128)
    course_name = forms.CharField(max_length=256)
    course_task_description = forms.CharField(label="Description")
