from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile


@admin.register(get_user_model())
class UserAdmin(AuthUserAdmin):
    inlines = [ProfileInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)
