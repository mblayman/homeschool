from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin

from homeschool.courses.models import Course, CourseResource, CourseTask, GradedWork


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(CourseTask)
class CourseTaskAdmin(OrderedModelAdmin):
    list_display = ("course", "description", "move_up_down_links")
    ordering = ("-id",)


@admin.register(GradedWork)
class GradedWorkAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(CourseResource)
class CourseResourceAdmin(admin.ModelAdmin):
    list_display = ("course", "title")
    ordering = ("-id",)
