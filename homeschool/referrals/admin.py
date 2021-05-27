from django.contrib import admin

from .models import Referral


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("id", "referring_user", "status")
    list_filter = ("status",)
    raw_id_fields = ("referring_user",)
