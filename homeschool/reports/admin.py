from django.contrib import admin

from .models import Bundle


@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    list_display = ("id", "school_year", "status")
    list_filter = ("status",)
