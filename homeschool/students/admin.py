from django.contrib import admin

from homeschool.students.models import Coursework, Enrollment, Grade, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id", "school", "first_name", "last_name")
    raw_id_fields = ("school",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "grade_level")


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("id", "student")


@admin.register(Coursework)
class CourseworkAdmin(admin.ModelAdmin):
    list_display = ("id", "course_task", "completed_date")
    raw_id_fields = ("course_task",)
