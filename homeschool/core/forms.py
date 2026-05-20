from django import forms
from django.db import transaction
from django.utils import timezone

from homeschool.courses.models import Course, CourseTask
from homeschool.schools import constants
from homeschool.schools.models import GradeLevel, SchoolYear
from homeschool.students.models import Enrollment, Student

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


class StartSetupForm(forms.Form):
    school_year_start_date = forms.DateField(label="Start Date")
    school_year_end_date = forms.DateField(label="End Date")
    grade_level_name = forms.CharField(label="Grade Level", max_length=128)
    student_first_name = forms.CharField(label="First Name", max_length=64)
    student_last_name = forms.CharField(label="Last Name", max_length=64)
    course_name = forms.CharField(label="Course", max_length=256)
    course_task_description = forms.CharField(label="Task", widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        today = kwargs.pop("today", timezone.localdate())
        super().__init__(*args, **kwargs)
        school_year_start_date = today.replace(month=9, day=1)
        school_year_start = (
            today.year if today <= school_year_start_date else today.year + 1
        )
        self.fields["school_year_start_date"].widget.attrs["placeholder"] = (
            f"9/1/{school_year_start}"
        )
        self.fields["school_year_end_date"].widget.attrs["placeholder"] = (
            f"6/1/{school_year_start + 1}"
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("school_year_start_date")
        end_date = cleaned_data.get("school_year_end_date")
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError(
                    "The start date must be before the end date."
                )

            delta = end_date - start_date
            if delta.days > constants.MAX_ALLOWED_DAYS:
                raise forms.ValidationError(
                    "A school year may not be longer than "
                    f"{constants.MAX_ALLOWED_DAYS} days."
                )
        return cleaned_data

    @transaction.atomic
    def save(self):
        school_year = SchoolYear.objects.create(
            school=self.user.school,
            start_date=self.cleaned_data["school_year_start_date"],
            end_date=self.cleaned_data["school_year_end_date"],
        )
        grade_level = GradeLevel.objects.create(
            school_year=school_year, name=self.cleaned_data["grade_level_name"]
        )
        student = Student.objects.create(
            school=self.user.school,
            first_name=self.cleaned_data["student_first_name"],
            last_name=self.cleaned_data["student_last_name"],
        )
        Enrollment.objects.create(student=student, grade_level=grade_level)
        course = Course.objects.create(name=self.cleaned_data["course_name"])
        course.grade_levels.add(grade_level)
        CourseTask.objects.create(
            course=course,
            description=self.cleaned_data["course_task_description"],
            duration=course.default_task_duration,
        )
        return school_year
