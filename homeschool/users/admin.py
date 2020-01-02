from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin


@admin.register(get_user_model())
class UserAdmin(AuthUserAdmin):
    pass
