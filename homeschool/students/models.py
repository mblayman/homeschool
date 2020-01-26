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


class Enrollment(models.Model):
    """The association between a student and grade level"""

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    grade_level = models.ForeignKey("schools.GradeLevel", on_delete=models.CASCADE)


class Coursework(models.Model):
    """The work that student completes for course tasks"""

    class Meta:
        verbose_name_plural = "coursework"

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_task = models.ForeignKey("courses.CourseTask", on_delete=models.CASCADE)
    completed_date = models.DateField()
