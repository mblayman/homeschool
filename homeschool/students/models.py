from django.db import models


class Student(models.Model):
    """The learner"""

    school = models.ForeignKey("schools.School", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name
