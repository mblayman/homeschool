from django.contrib import admin
from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline

from homeschool.courses.models import GradeLevelCoursesThroughModel
from homeschool.schools.models import GradeLevel, School, SchoolBreak, SchoolYear


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("id", "admin")


@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ("id", "school", "start_date")
    search_fields = ("id",)


class GradeLevelCoursesThroughModelTabularInline(OrderedTabularInline):
    model = GradeLevelCoursesThroughModel
    fields = ("course", "order", "move_up_down_links")
    readonly_fields = ("order", "move_up_down_links")
    extra = 0
    ordering = ("order",)


@admin.register(GradeLevel)
class GradeLevelAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    list_display = ("school_year", "name")
    inlines = (GradeLevelCoursesThroughModelTabularInline,)


@admin.register(SchoolBreak)
class SchoolBreakAdmin(admin.ModelAdmin):
    list_display = ("school_year", "start_date", "end_date")
