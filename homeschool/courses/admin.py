from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin

from homeschool.courses.models import Course, CourseResource, CourseTask, GradedWork


class CourseTaskInline(admin.TabularInline):
    model = CourseTask
    fields = ["description", "order"]
    readonly_fields = ["description", "order"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [CourseTaskInline]


@admin.register(CourseTask)
class CourseTaskAdmin(OrderedModelAdmin):
    list_display = ("course", "description", "order", "move_up_down_links")
    ordering = ("-id",)


@admin.register(GradedWork)
class GradedWorkAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(CourseResource)
class CourseResourceAdmin(admin.ModelAdmin):
    list_display = ("course", "title")
    ordering = ("-id",)
