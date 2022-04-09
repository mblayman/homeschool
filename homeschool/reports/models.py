from __future__ import annotations

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from hashid_field import HashidAutoField


def report_path(bundle, filename):
    """The path to the report bundle"""
    school = bundle.school_year.school
    return f"user_{school.admin_id}/bundles/{bundle.school_year.id}/{filename}"


class BundleQuerySet(models.QuerySet):
    def pending(self) -> BundleQuerySet:
        return self.filter(status=self.model.Status.PENDING)


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

    objects = BundleQuerySet.as_manager()

    def store(self, report_data: bytes) -> None:
        """Store the report data into the bundle."""
        name = f"School Desk bundle {self.school_year}.zip"
        # The "dash" character is an emdash from the SchoolYear.__str__ method.
        # Replace with a regular dash to avoid header character encoding weirdness.
        name = name.replace("–", "-")

        self.report = ContentFile(report_data, name=name)
        self.status = self.Status.COMPLETE
        self.save()
