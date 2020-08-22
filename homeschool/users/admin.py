from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from hijack.helpers import login_user


@admin.register(get_user_model())
class UserAdmin(AuthUserAdmin):
    actions = ["hijack_user"]

    def hijack_user(self, request, queryset):
        """Hijack a user."""
        if len(queryset) == 1:
            user = queryset[0]
            return login_user(request, user)
