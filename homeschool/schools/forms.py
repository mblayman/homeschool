from django import forms

from .models import SchoolYear


class SchoolYearForm(forms.ModelForm):
    class Meta:
        model = SchoolYear
        fields = ["school", "start_date", "end_date"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        school = self.cleaned_data.get("school")
        if school != self.user.school:
            raise forms.ValidationError(
                "A school year cannot be created for a different school."
            )

        start_date = self.cleaned_data["start_date"]
        end_date = self.cleaned_data["end_date"]
        if start_date >= end_date:
            raise forms.ValidationError("The start date must be before the end date.")
        return self.cleaned_data
