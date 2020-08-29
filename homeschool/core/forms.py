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

    def save(self, *args, **kwargs):
        """Save the model instance and the days of week."""
        days_of_week = 0
        day_field_to_model_day = {
            "sunday": DaysOfWeekModel.SUNDAY,
            "monday": DaysOfWeekModel.MONDAY,
            "tuesday": DaysOfWeekModel.TUESDAY,
            "wednesday": DaysOfWeekModel.WEDNESDAY,
            "thursday": DaysOfWeekModel.THURSDAY,
            "friday": DaysOfWeekModel.FRIDAY,
            "saturday": DaysOfWeekModel.SATURDAY,
        }
        for day_field, model_day in day_field_to_model_day.items():
            if self.cleaned_data.get(day_field):
                days_of_week += model_day
        self.instance.days_of_week = days_of_week
        return super().save(*args, **kwargs)
