import uuid

from django import forms

from .models import User
from .tasks import generate_magic_link


class SiginForm(forms.Form):
    email = forms.EmailField()

    def save(self):
        """Create a user if it doesn't exist, then trigger the magic link job."""
        email = self.cleaned_data["email"]
        user, _ = User.objects.get_or_create(
            email=email, defaults={"username": str(uuid.uuid4())}
        )
        generate_magic_link(user.id)
