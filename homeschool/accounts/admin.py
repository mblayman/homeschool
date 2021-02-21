from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Account


@admin.register(Account)
class AccountAdmin(SimpleHistoryAdmin):
    list_display = ("id", "user", "status")
    list_filter = ("status",)
    raw_id_fields = ("user",)
