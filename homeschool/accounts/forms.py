import uuid

from django import forms
from django.conf import settings

from .models import User
from .tasks import generate_magic_link
from .turnstile import verify_turnstile_token


class SiginForm(forms.Form):
    email = forms.EmailField()

    def __init__(self, *args, remote_ip: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.remote_ip = remote_ip

    def clean(self):
        cleaned_data = super().clean()
        if not settings.TURNSTILE_ENABLED:
            return cleaned_data

        token = str(self.data.get("cf-turnstile-response") or "")
        if not verify_turnstile_token(token, self.remote_ip):
            raise forms.ValidationError(
                "Please confirm you are human before continuing."
            )

        return cleaned_data

    def save(self):
        """Create a user if it doesn't exist, then trigger the magic link job."""
        email = self.cleaned_data["email"]
        user, _ = User.objects.get_or_create(
            email=email, defaults={"username": str(uuid.uuid4())}
        )
        generate_magic_link(user.id)
