from django.contrib import admin

from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status")
    list_filter = ("status",)
    raw_id_fields = ("user",)
