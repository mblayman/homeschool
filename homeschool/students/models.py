import uuid

from django.db import models


class Student(models.Model):
    """The learner"""

    school = models.ForeignKey(
        "schools.School", on_delete=models.CASCADE, related_name="students"
    )
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)

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

    def get_week_coursework(self, week):
        """Get the coursework completed in the week.

        The data is in a dictionary for fast lookups.
        """
        week_coursework = {}
        coursework_qs = Coursework.objects.filter(
            student=self, completed_date__range=week
        ).select_related("course_task")
        for coursework in coursework_qs:
            course_id = coursework.course_task.course_id
            if course_id not in week_coursework:
                week_coursework[course_id] = {}

            if coursework.completed_date not in week_coursework[course_id]:
                # It's possible for multiple coursework items to share the same
                # completion day because that's controlled by user input.
                week_coursework[course_id][coursework.completed_date] = []

            week_coursework[course_id][coursework.completed_date].append(coursework)

        return week_coursework

    def get_day_coursework(self, day):
        """Get the coursework completed in the week.

        The data is in a dictionary for fast lookups.
        """
        day_coursework = {}
        coursework_qs = Coursework.objects.filter(
            student=self, completed_date=day
        ).select_related("course_task")
        for coursework in coursework_qs:
            course_id = coursework.course_task.course_id
            if course_id not in day_coursework:
                # It's possible for multiple coursework items to share the same
                # completion day because that's controlled by user input.
                day_coursework[course_id] = []

            day_coursework[course_id].append(coursework)

        return day_coursework


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
