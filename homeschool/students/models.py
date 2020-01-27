from django.db import models


class Student(models.Model):
    """The learner"""

    school = models.ForeignKey(
        "schools.School", on_delete=models.CASCADE, related_name="students"
    )
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

    def get_courses(self, school_year):
        """Get the courses from the school year."""
        enrollment = Enrollment.objects.filter(
            student=self, grade_level__in=school_year.grade_levels.all()
        ).first()
        if enrollment:
            # This looks goofy, but it operates under the assumption
            # school year did all the prefetching on grade levels and courses.
            for grade_level in school_year.grade_levels.all():
                if grade_level.id == enrollment.grade_level_id:
                    return list(grade_level.courses.all())
        return []


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
    completed_date = models.DateField(db_index=True)
