from django.contrib import admin

from homeschool.courses.models import Course, CourseTask


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(CourseTask)
class CourseTaskAdmin(admin.ModelAdmin):
    list_display = ("course", "description")
