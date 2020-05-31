from django import forms

from homeschool.core.forms import DaysOfWeekModelForm

from .models import GradeLevel, SchoolYear


class GradeLevelForm(forms.ModelForm):
    class Meta:
        model = GradeLevel
        fields = ["school_year", "name"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        school_year = self.cleaned_data.get("school_year")
        if not school_year:
            raise forms.ValidationError("Invalid school year.")

        if not SchoolYear.objects.filter(
            id=school_year.id, school__admin=self.user
        ).exists():
            raise forms.ValidationError(
                "A grade level cannot be created for a different user's school year."
            )

        return self.cleaned_data


class SchoolYearForm(DaysOfWeekModelForm):
    class Meta:
        model = SchoolYear
        fields = [
            "school",
            "start_date",
            "end_date",
        ] + DaysOfWeekModelForm.days_of_week_fields

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        school = self.cleaned_data.get("school")
        if school != self.user.school:
            raise forms.ValidationError(
                "A school year cannot be created for a different school."
            )

        start_date = self.cleaned_data.get("start_date")
        end_date = self.cleaned_data.get("end_date")
        if start_date and end_date:
            if start_date >= end_date:
                self.add_error(None, "The start date must be before the end date.")
            self.check_overlap(start_date, end_date)

        has_week_days = any(
            [
                bool(self.cleaned_data.get(field))
                for field in DaysOfWeekModelForm.days_of_week_fields
            ]
        )
        if not has_week_days:
            self.add_error(None, "A school year must run on at least one week day.")

        return self.cleaned_data

    def check_overlap(self, start_date, end_date):
        """Check if the dates overlap with any of the user's existing school years."""
        overlapping_school_years = SchoolYear.objects.filter(
            school=self.user.school, start_date__lte=end_date, end_date__gte=start_date
        )

        # When updating, be sure to exclude the existing school year
        # or it will overlap with itself.
        if self.instance:
            overlapping_school_years = overlapping_school_years.exclude(
                id=self.instance.id
            )

        school_year = overlapping_school_years.first()
        if school_year:
            self.add_error(
                None,
                "School years may not have overlapping dates. "
                f"The dates provided overlap with the {school_year} school year.",
            )
