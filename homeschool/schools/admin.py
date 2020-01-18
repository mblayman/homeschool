from django.contrib import admin

from homeschool.schools.models import GradeLevel, School, SchoolYear


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("admin",)


@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ("school", "start_date")


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ("school_year", "name")
