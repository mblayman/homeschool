from django import forms

from homeschool.core.forms import DaysOfWeekModelForm
from homeschool.courses.models import Course

from .models import GradeLevel, SchoolBreak, SchoolYear


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


class SchoolBreakForm(forms.ModelForm):
    class Meta:
        model = SchoolBreak
        fields = ["school_year", "description", "start_date", "end_date"]

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
                "A school break cannot be created for a different user's school year."
            )

        start_date = self.cleaned_data.get("start_date")
        end_date = self.cleaned_data.get("end_date")
        if start_date and end_date:
            if start_date > end_date:
                self.add_error(None, "The start date must be before the end date.")
            else:
                self.check_in_school_year(school_year, start_date, end_date)
                self.check_overlap(school_year, start_date, end_date)

        return self.cleaned_data

    def check_in_school_year(self, school_year, start_date, end_date):
        """Check that the break fits in the school year."""

        if start_date < school_year.start_date:
            self.add_error(
                None,
                "A break must be in the school year. "
                f"{start_date} is before the school year's start "
                f"of {school_year.start_date}.",
            )

        if end_date > school_year.end_date:
            self.add_error(
                None,
                "A break must be in the school year. "
                f"{end_date} is after the school year's end "
                f"of {school_year.end_date}.",
            )

    def check_overlap(self, school_year, start_date, end_date):
        """Check if the dates overlap with any of the user's existing school breaks."""
        overlapping_school_breaks = SchoolBreak.objects.filter(
            school_year=school_year, start_date__lte=end_date, end_date__gte=start_date
        )

        # When updating, be sure to exclude the existing school break
        # or it will overlap with itself.
        if self.instance:
            overlapping_school_breaks = overlapping_school_breaks.exclude(
                id=self.instance.id
            )

        school_break = overlapping_school_breaks.first()
        if school_break:
            self.add_error(
                None,
                "School breaks may not have overlapping dates. "
                "The dates provided overlap with the school break "
                f"from {school_break.start_date} to {school_break.end_date}.",
            )


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
            else:
                self.check_overlap(start_date, end_date)
                self.check_max_length(start_date, end_date)
                self.check_breaks(start_date, end_date)

        days_of_week = self.get_days_of_week()
        if days_of_week == SchoolYear.NO_DAYS:
            self.add_error(None, "A school year must run on at least one week day.")

        self.check_superset_of_courses(days_of_week)

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

    def check_max_length(self, start_date, end_date):
        """Check that the school year is within the max allowed days."""
        max_allowed_days = 500
        delta = end_date - start_date
        if abs(delta.days) > max_allowed_days:
            self.add_error(
                None, f"A school year may not be longer than {max_allowed_days} days."
            )

    def check_breaks(self, start_date, end_date):
        """Check that the school year continues to contain any breaks."""
        if SchoolBreak.objects.filter(
            school_year=self.instance, start_date__lt=start_date
        ).exists():
            self.add_error(
                None, "You have a school break before the school year's start date."
            )
        if SchoolBreak.objects.filter(
            school_year=self.instance, end_date__gt=end_date
        ).exists():
            self.add_error(
                None, "You have a school break after the school year's end date."
            )

    def check_superset_of_courses(self, days_of_week):
        """Check that the days of week are a superset of any existing courses days."""
        if self.instance.id is None:
            return

        courses = Course.objects.filter(
            grade_levels__school_year=self.instance
        ).distinct()
        self.instance.days_of_week = days_of_week
        superset_courses = [
            course
            for course in courses
            if not self.instance.is_superset(course.days_of_week)
        ]
        if superset_courses:
            courses_str = ", ".join(map(str, superset_courses))
            self.add_error(
                None,
                "The school year days must include any days that a course runs."
                " The following courses run on more days than the school year:"
                f" {courses_str}",
            )
