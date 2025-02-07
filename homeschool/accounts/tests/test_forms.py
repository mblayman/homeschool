import pytest

from homeschool.accounts.forms import SiginForm
from homeschool.accounts.models import User


@pytest.mark.usefixtures("db")
class TestSigninForm:
    def test_create_user(self, mailoutbox):
        """A non-existing email creates a new User record."""
        # Check the username uniqueness constraint.
        User.objects.create(email="somethingelse@somewhere.com")
        email = "newuser@somewhere.com"
        data = {"email": email}
        form = SiginForm(data=data)
        is_valid = form.is_valid()

        form.save()
        # Ensure only 1 account is created.
        form.save()

        assert is_valid
        assert User.objects.filter(email=email).count() == 1
        assert mailoutbox

    def test_existing_user(self):
        """When a user account exists for an email, use that user."""
        user = User.objects.create(email="test@testing.com")
        data = {"email": user.email}
        form = SiginForm(data=data)
        is_valid = form.is_valid()

        form.save()

        assert is_valid
        assert User.objects.filter(email=user.email).count() == 1

    def test_invalid_email(self):
        """An invalid email is rejected."""
        data = {"email": "not-an-email"}
        form = SiginForm(data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "valid email" in form.errors["email"][0]
