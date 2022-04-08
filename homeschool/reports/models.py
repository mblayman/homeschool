from django.conf import settings
from django.db import models
from hashid_field import HashidAutoField


def report_path(bundle, filename):
    """The path to the report bundle"""
    school = bundle.school_year.school
    return f"user_{school.admin_id}/bundles/{bundle.school_year.id}/{filename}"


class Bundle(models.Model):
    """A bundle of PDF reports that show the end-of-year results of a school year"""

    class Status(models.IntegerChoices):
        PENDING = 1
        COMPLETE = 2

    id = HashidAutoField(primary_key=True, salt=f"bundle{settings.HASHID_FIELD_SALT}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    school_year = models.ForeignKey("schools.SchoolYear", on_delete=models.CASCADE)
    report = models.FileField(upload_to=report_path)
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)
