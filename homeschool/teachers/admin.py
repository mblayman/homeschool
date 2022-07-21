from django.contrib import admin

from .models import Checklist


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ("id", "school_year")
    raw_id_fields = ("school_year",)
